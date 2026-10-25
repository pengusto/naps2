/* Test process only. Never packaged. No USB imports. MIT. */
#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
int main(int argc, char **argv) {
    if (argc != 3 || strcmp(argv[1], "--listen")) return 64;
    char path[4096]; snprintf(path,sizeof(path),"%s.pid",argv[2]);
    FILE *f=fopen(path,"w"); if (!f) return 1; fprintf(f,"%d",getpid()); fclose(f);
    if (strstr(argv[2],"retry-before")) { puts("retry\tmissing"); return 75; }
    printf("ready\tepsonds:libusb:001:005\n"); fflush(stdout);
    struct timespec delay={0,250000000};
    if (strstr(argv[2],"hold")) { for (;;) nanosleep(&delay,NULL); }
    if (strstr(argv[2],"eof")) return strstr(argv[2],"fail-eof") ? 1 : 0;
    if (strstr(argv[2],"disconnect")) { puts("retry\tdisconnected"); return 75; }
    if (strstr(argv[2],"bad-retry")) { puts("retry\tbusy"); return 0; }
    if (strstr(argv[2],"ui-data")) {
        snprintf(path,sizeof(path),"%s.trigger",argv[2]);
        while (access(path,F_OK)) nanosleep(&delay,NULL);
        if (unlink(path)) return 1;
    }
    printf("button\t0\t%s\n",strstr(argv[2],"bad")?"wrong":"epsonds:libusb:001:005"); fflush(stdout);
    if (strstr(argv[2],"multiple")) puts("button\t0\tepsonds:libusb:001:005");
    nanosleep(&delay,NULL);
    snprintf(path,sizeof(path),"%s.released",argv[2]);
    f=fopen(path,"w"); if (!f) return 1; fputs("released",f); fclose(f);
    return 0;
}
