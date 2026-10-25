/* Private offline fixture, 2026-10-19. Original code, MIT (repository LICENSE).
 * No SANE/USB code. Used only in a separate signed replay app, never production.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv)
{
    const char *name = getenv("NAPS2_TEST_REPLAY_DEVICE_NAME");
    if (!name) name = "Epson ES-60W";
    const char *device = getenv("NAPS2_TEST_REPLAY_DEVICE_ID");
    if (!device) device = "epsonds:libusb:fixture:001";
    char argument[128];
    if (snprintf(argument, sizeof argument, "--device-name=%s", device) >= (int)sizeof argument) return 64;
    if (argc == 2 && strncmp(argv[1], "--formatted-device-list=", 24) == 0) {
        printf("%s\t%s\n", device, name); return 0;
    }
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        puts("offline TIFF replay fixture; no scanner backend"); return 0;
    }
    const char *expected[] = {argument, "--format=tiff",
        "--source=ADF Front", "--mode=Color", "--depth=8", "--resolution=300",
        "-l", "0", "-t", "0", "-x", "215.89999389648438", "-y", "355.59999084472656",
        "--es60w-auto-length=yes"};
    if (argc != 16) return 64;
    for (int i = 1; i < argc; ++i) if (strcmp(argv[i], expected[i - 1])) return 64;
    const char *path = getenv("NAPS2_TEST_REPLAY_TIFF");
    if (!path || path[0] != '/') return 78;
    FILE *in = fopen(path, "rb"); if (!in) return 74;
    unsigned char buffer[65536]; size_t n;
    while ((n = fread(buffer, 1, sizeof buffer, in)))
        if (fwrite(buffer, 1, n, stdout) != n) { fclose(in); return 74; }
    int failed = ferror(in); fclose(in);
    fprintf(stderr, "OFFLINE REPLAY ONLY; scanner not accessed\n");
    return failed ? 74 : 0;
}
