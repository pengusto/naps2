/* Original code, MIT. Normal use has no diagnostic prerequisites.
 * An explicitly requested diagnostic directory retains the strict private logger.
 */
#define main diagnostic_main
#include "TransportLogLauncher.c"
#undef main

int main(int argc, char **argv)
{
    if (getenv("NAPS2_TEST_TRANSPORT_LOG_DIR")) return diagnostic_main(argc, argv);
    char executable[PATH_MAX];
    uint32_t size = sizeof executable;
    if (_NSGetExecutablePath(executable, &size)) return 78;
    char *slash = strrchr(executable, '/');
    if (!slash || (size_t)(slash - executable) + sizeof "/scanimage-real" > sizeof executable) return 78;
    strcpy(slash, "/scanimage-real");
    argv[0] = executable;
    execv(executable, argv);
    perror("scanimage-real");
    return errno == ENOENT ? 127 : 126;
}
