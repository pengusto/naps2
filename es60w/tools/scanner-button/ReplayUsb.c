/* Own test-only libusb substitute for the real receiver source. No device I/O. MIT. */
#include <libusb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int opened, claimed, reads;
static const char *scenario(void) { const char *s=getenv("NAPS2_BUTTON_REPLAY_CASE"); return s?s:""; }
static int is(const char *name) { return strcmp(scenario(),name)==0; }
int libusb_init(libusb_context **ctx) { *ctx=(libusb_context*)1; return 0; }
ssize_t libusb_get_device_list(libusb_context *ctx, libusb_device ***list) {
    (void)ctx; static libusb_device *devices[]={(libusb_device*)1,(libusb_device*)2,NULL};
    if (reads >= 3 && is("io-gone")) { *list=devices+2; return 0; }
    if (reads >= 3 && is("io-replaced")) { *list=devices+1; return 1; }
    if (reads >= 3 && is("io-enumeration-error")) return LIBUSB_ERROR_OTHER;
    *list=devices; return is("missing")?0:is("ambiguous")?2:1;
}
int libusb_get_device_descriptor(libusb_device *dev, struct libusb_device_descriptor *d) {
    (void)dev; memset(d,0,sizeof(*d)); d->idVendor=0x04b8; d->idProduct=0x016e; return 0;
}
int libusb_get_active_config_descriptor(libusb_device *dev, struct libusb_config_descriptor **config) {
    (void)dev;
    static struct libusb_endpoint_descriptor endpoints[]={
        {.bEndpointAddress=0x81,.bmAttributes=LIBUSB_TRANSFER_TYPE_BULK,.wMaxPacketSize=512},
        {.bEndpointAddress=0x02,.bmAttributes=LIBUSB_TRANSFER_TYPE_BULK,.wMaxPacketSize=512},
        {.bEndpointAddress=0x83,.bmAttributes=LIBUSB_TRANSFER_TYPE_INTERRUPT,.wMaxPacketSize=8}};
    static struct libusb_interface_descriptor desc={.bInterfaceNumber=0,.bAlternateSetting=0,.bNumEndpoints=3,.endpoint=endpoints};
    static struct libusb_interface interface={.altsetting=&desc,.num_altsetting=1};
    static struct libusb_config_descriptor conf={.bNumInterfaces=1,.interface=&interface};
    if(is("config-gone")) return LIBUSB_ERROR_NO_DEVICE;
    *config=&conf; return 0;
}
void libusb_free_config_descriptor(struct libusb_config_descriptor *config) { (void)config; }
int libusb_open(libusb_device *dev, libusb_device_handle **handle) {
    (void)dev; if(is("open-gone")) return LIBUSB_ERROR_NO_DEVICE;
    opened++; *handle=(libusb_device_handle*)1; return 0;
}
int libusb_claim_interface(libusb_device_handle *handle, int interface) {
    (void)handle; (void)interface;
    if(is("claim-gone")) return LIBUSB_ERROR_NO_DEVICE;
    if(is("busy")) return LIBUSB_ERROR_BUSY;
    claimed++; return 0;
}
uint8_t libusb_get_bus_number(libusb_device *dev) { (void)dev; return 1; }
uint8_t libusb_get_device_address(libusb_device *dev) { return dev==(libusb_device*)2?10:9; }
int libusb_interrupt_transfer(libusb_device_handle *handle, unsigned char endpoint,
        unsigned char *data, int length, int *transferred, unsigned int timeout) {
    (void)handle;
    if(endpoint!=0x83 || length!=8 || timeout!=250 || !opened || !claimed) abort();
    int n=reads++; *transferred=0;
    if(is("read-gone")) return n<2?LIBUSB_ERROR_TIMEOUT:LIBUSB_ERROR_NO_DEVICE;
    if(is("io-gone") || is("io-replaced") || is("io-enumeration-error") || is("io-present"))
        return n<2?LIBUSB_ERROR_TIMEOUT:LIBUSB_ERROR_IO;
    if(is("badread")) return LIBUSB_ERROR_IO;
    if(!is("noise-press") || n>7) abort();
    if(n==1 || n==3 || n==4) return LIBUSB_ERROR_TIMEOUT;
    data[0]=(n==2 || n==5)?3:1; data[1]=0; *transferred=2;
    return 0;
}
int libusb_release_interface(libusb_device_handle *handle, int interface) {
    (void)handle; (void)interface; if(claimed!=1) abort(); claimed--; return 0;
}
void libusb_close(libusb_device_handle *handle) { (void)handle; if(opened!=1 || claimed) abort(); opened--; }
void libusb_free_device_list(libusb_device **list, int unref) { (void)list; (void)unref; }
void libusb_exit(libusb_context *ctx) {
    (void)ctx; if(opened || claimed) abort();
    fprintf(stderr,"replay-cleanup opened=%d claimed=%d reads=%d\n",opened,claimed,reads);
}
const char *libusb_error_name(int code) { (void)code; return "TEST-ONLY-USB-ERROR"; }
