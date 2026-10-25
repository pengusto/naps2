/* Own ES-60W interrupt receiver. MIT. No Epson library, bulk/scan command or driver install. */
#define _POSIX_C_SOURCE 200809L
#define _DARWIN_C_SOURCE
#include <libusb.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

static volatile sig_atomic_t stopped;
static void stop_handler(int sig) { (void)sig; stopped = 1; }
/* Darwin may report IO instead of NO_DEVICE on removal. Only retry it as
 * disconnected if the original bus/address has actually disappeared. No USB
 * requests, resets or scan commands are issued by this enumeration check. */
static int connection_missing(libusb_context *ctx, libusb_device *original) {
    unsigned char bus = libusb_get_bus_number(original);
    unsigned char address = libusb_get_device_address(original);
    libusb_device **current = NULL;
    ssize_t count = libusb_get_device_list(ctx, &current);
    if (count < 0) return 0;
    int found = 0;
    for (ssize_t i = 0; i < count; ++i)
        if (libusb_get_bus_number(current[i]) == bus
            && libusb_get_device_address(current[i]) == address) found = 1;
    libusb_free_device_list(current, 1);
    return !found;
}
/* Observed protocol discriminator; unobserved packet lengths/other events never start a scan. */
static int button_packet(const unsigned char *p, int n) {
    return n >= 2 && n <= 8 && p[0] == 1 ? p[1] : -1;
}
typedef struct { int quiet, armed; } event_gate;
enum { NO_EVENT = -1, BECAME_READY = -2 };
/* Opening a receiver must not turn a queued/held previous press into a new scan. */
static int receive_event(event_gate *gate, const unsigned char *p, int n, int timeout) {
    if (timeout) {
        if (!gate->armed && ++gate->quiet >= 2) { gate->armed = 1; return BECAME_READY; }
        return NO_EVENT;
    }
    if (!gate->armed) { gate->quiet = 0; return NO_EVENT; }
    return button_packet(p, n);
}
static int self_test(void) {
    unsigned char p[9] = {1, 0}; int cases = 0;
    for (int n = 0; n <= 9; ++n) {
        if (button_packet(p, n) != (n >= 2 && n <= 8 ? 0 : -1)) return 1;
        ++cases;
    }
    for (int type = 0; type < 256; ++type) {
        p[0] = (unsigned char)type; p[1] = 3;
        if (button_packet(p, 8) != (type == 1 ? 3 : -1)) return 1;
        ++cases;
    }
    event_gate gate = {0,0}; unsigned char press[2] = {1,0}, other[2] = {3,0};
    int checks = 0;
    if (receive_event(&gate, press, 2, 0) != NO_EVENT) return 1; checks++;
    if (receive_event(&gate, NULL, 0, 1) != NO_EVENT) return 1; checks++;
    if (receive_event(&gate, press, 2, 0) != NO_EVENT) return 1; checks++;
    if (receive_event(&gate, NULL, 0, 1) != NO_EVENT) return 1; checks++;
    if (receive_event(&gate, NULL, 0, 1) != BECAME_READY) return 1; checks++;
    if (receive_event(&gate, other, 2, 0) != NO_EVENT) return 1; checks++;
    if (receive_event(&gate, NULL, 0, 1) != NO_EVENT) return 1; checks++;
    if (receive_event(&gate, press, 2, 0) != 0) return 1; checks++;
    printf("{\"parser_cases\":%d,\"gate_cases\":%d,\"usb_initialized\":false,\"scan_commands\":0}\n", cases, checks);
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--self-test") == 0) return self_test();
    if (argc != 3 || strcmp(argv[1], "--listen") != 0) {
        fprintf(stderr, "usage: scanner-button --listen PRIVATE_LOCK_FILE | --self-test\n"); return 64;
    }
    signal(SIGTERM, stop_handler); signal(SIGINT, stop_handler);
    int lockfd = open(argv[2], O_CREAT | O_RDWR | O_NOFOLLOW, 0600);
    struct stat st;
    if (lockfd < 0 || fstat(lockfd, &st) || !S_ISREG(st.st_mode) || st.st_uid != getuid()
        || st.st_nlink != 1 || (st.st_mode & 077) || flock(lockfd, LOCK_EX | LOCK_NB)) {
        fprintf(stderr, "Button receiver already active or private lock unavailable\n");
        if (lockfd >= 0) close(lockfd); return 65;
    }
    libusb_context *ctx = NULL; libusb_device **devices = NULL;
    libusb_device_handle *handle = NULL;
    int result = 1, claimed = -1, selected = -1, candidates = 0;
    unsigned char endpoint = 0; char device_id[80] = {0}; pid_t parent = getppid();
    const char *retry = NULL;
    if (libusb_init(&ctx)) goto done;
    ssize_t count = libusb_get_device_list(ctx, &devices);
    if (count < 0) goto done;
    for (ssize_t i = 0; i < count; ++i) {
        struct libusb_device_descriptor desc;
        if (!libusb_get_device_descriptor(devices[i], &desc)
            && desc.idVendor == 0x04b8 && desc.idProduct == 0x016e) {
            selected = (int)i; ++candidates;
        }
    }
    if (candidates != 1) {
        if (candidates == 0) { retry = "missing"; result = 75; goto done; }
        fprintf(stderr, "Exactly one USB ES-60W is required (found %d)\n", candidates); goto done;
    }
    struct libusb_config_descriptor *config = NULL;
    int config_rc = libusb_get_active_config_descriptor(devices[selected], &config);
    if (config_rc) {
        if (config_rc == LIBUSB_ERROR_NO_DEVICE) { retry = "disconnected"; result = 75; }
        goto done;
    }
    int iface = -1;
    for (int i = 0; i < config->bNumInterfaces; ++i) {
        /* Never change configuration/alternate setting or detach a kernel driver. */
        for (int a = 0; a < config->interface[i].num_altsetting; ++a) {
            const struct libusb_interface_descriptor *d = &config->interface[i].altsetting[a];
            if (d->bAlternateSetting != 0) continue;
            int bulk_in = 0, bulk_out = 0; unsigned char interrupt_in = 0;
            for (int e = 0; e < d->bNumEndpoints; ++e) {
                const struct libusb_endpoint_descriptor *ep = &d->endpoint[e];
                int in = (ep->bEndpointAddress & LIBUSB_ENDPOINT_DIR_MASK) == LIBUSB_ENDPOINT_IN;
                int type = ep->bmAttributes & LIBUSB_TRANSFER_TYPE_MASK;
                if (type == LIBUSB_TRANSFER_TYPE_BULK) { if (in) bulk_in++; else bulk_out++; }
                if (type == LIBUSB_TRANSFER_TYPE_INTERRUPT && in && ep->wMaxPacketSize >= 2)
                    interrupt_in = ep->bEndpointAddress;
            }
            if (bulk_in && bulk_out && interrupt_in) {
                if (iface != -1) { iface = -2; break; }
                iface = d->bInterfaceNumber; endpoint = interrupt_in;
            }
        }
        if (iface == -2) break;
    }
    libusb_free_config_descriptor(config);
    if (iface < 0) { fprintf(stderr, "No unambiguous scanner interrupt endpoint\n"); goto done; }
    int rc = libusb_open(devices[selected], &handle);
    if (rc == LIBUSB_ERROR_NO_DEVICE) { retry = "disconnected"; result = 75; goto done; }
    if (rc) { fprintf(stderr, "Cannot open USB scanner: %s\n", libusb_error_name(rc)); goto done; }
    rc = libusb_claim_interface(handle, iface);
    if (rc == LIBUSB_ERROR_BUSY || rc == LIBUSB_ERROR_NO_DEVICE) {
        retry = rc == LIBUSB_ERROR_BUSY ? "busy" : "disconnected"; result = 75; goto done;
    }
    if (rc) { fprintf(stderr, "Scanner interface busy/unavailable: %s\n", libusb_error_name(rc)); goto done; }
    claimed = iface;
    snprintf(device_id, sizeof(device_id), "epsonds:libusb:%03u:%03u",
             libusb_get_bus_number(devices[selected]), libusb_get_device_address(devices[selected]));
    fprintf(stderr, "receiver-open device=%s endpoint=0x%02x; draining until quiet\n", device_id, endpoint);
    event_gate gate = {0,0};
    int button = -1;
    while (!stopped && getppid() == parent) {
        unsigned char packet[8] = {0}; int transferred = 0;
        rc = libusb_interrupt_transfer(handle, endpoint, packet, sizeof(packet), &transferred, 250);
        if (rc == LIBUSB_ERROR_INTERRUPTED) continue;
        if (rc == LIBUSB_ERROR_TIMEOUT) {
            if (receive_event(&gate, NULL, 0, 1) == BECAME_READY) {
                printf("ready\t%s\n", device_id); fflush(stdout);
            }
            continue;
        }
        if (rc == LIBUSB_ERROR_NO_DEVICE) { retry = "disconnected"; result = 75; goto done; }
        if (rc == LIBUSB_ERROR_IO && connection_missing(ctx, devices[selected])) {
            fprintf(stderr, "Interrupt IO after original USB connection disappeared; reopening\n");
            retry = "disconnected"; result = 75; goto done;
        }
        if (rc) { fprintf(stderr, "Interrupt read ended: %s\n", libusb_error_name(rc)); goto done; }
        fprintf(stderr, "interrupt n=%d bytes=", transferred);
        for (int k = 0; k < transferred && k < 8; k++) fprintf(stderr, "%02x", packet[k]);
        fprintf(stderr, " armed=%d\n", gate.armed);
        button = receive_event(&gate, packet, transferred, 0);
        if (button >= 0) break;
    }
    result = 0;
    /* Close the interface BEFORE announcing a button. The app also awaits process exit. */
    libusb_release_interface(handle, claimed); claimed = -1;
    libusb_close(handle); handle = NULL;
    if (!stopped && getppid() == parent && button >= 0) printf("button\t%d\t%s\n", button, device_id);
done:
    if (handle) {
        if (claimed >= 0) libusb_release_interface(handle, claimed);
        libusb_close(handle);
    }
    if (devices) libusb_free_device_list(devices, 1);
    if (ctx) libusb_exit(ctx);
    close(lockfd);
    if (retry && !stopped && getppid() == parent) printf("retry\t%s\n", retry);
    return result;
}
