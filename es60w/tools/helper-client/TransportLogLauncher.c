/* Private diagnostic launcher, 2026-10-19. Original code, MIT (repository LICENSE).
 * Preserves scanimage's stdout/exit status; writes stderr to a new private file.
 * Explicit log directory is required: no silently unlogged physical scan.
 */
#include <mach-o/dyld.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    (void)argc;
    const char *directory = getenv("NAPS2_TEST_TRANSPORT_LOG_DIR");
    char resolved[PATH_MAX], log[PATH_MAX], executable[PATH_MAX];
    struct stat st;
    if (!directory || directory[0] != '/' || !realpath(directory, resolved) ||
        stat(resolved, &st) || !S_ISDIR(st.st_mode) || st.st_uid != getuid() ||
        (st.st_mode & 077)) {
        fprintf(stderr, "Transport test requires an owned 0700 NAPS2_TEST_TRANSPORT_LOG_DIR\n");
        return 78;
    }
    int n = snprintf(log, sizeof log, "%s/epsonds-XXXXXX", resolved);
    if (n < 0 || n >= (int)sizeof log) return 78;
    int fd = mkstemp(log);
    if (fd < 0) { perror("transport log"); return 78; }
    if (fchmod(fd, 0600) || dup2(fd, STDERR_FILENO) < 0) {
        close(fd); return 78;
    }
    close(fd);
    if (setenv("SANE_DEBUG_EPSONDS", "20", 1)) return 78;
    uint32_t size = sizeof executable;
    if (_NSGetExecutablePath(executable, &size)) return 78;
    char *slash = strrchr(executable, '/');
    if (!slash || (size_t)(slash - executable) + sizeof "/scanimage-real" > sizeof executable)
        return 78;
    strcpy(slash, "/scanimage-real");
    argv[0] = executable;
    execv(executable, argv);
    perror("scanimage-real");
    return errno == ENOENT ? 127 : 126;
}
