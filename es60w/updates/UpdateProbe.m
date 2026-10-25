// Copyright (c) 2026 Pengusto. MIT; see ../LICENSE-tools.txt.
// OFFLINE TEST ONLY: never embed this automated user driver in a release app.
#import "UpdaterBridge.m"

static NSString *testMode;
static NSString *resultFile;
static NSMutableArray *events;
static int busy;
static int canInstall(void) { return !busy; }
static void event(NSString *name) {
    [events addObject:name];
    [events writeToFile:resultFile atomically:YES];
}
static void finish(NSString *name) { event(name); [NSApp terminate:nil]; }

@interface Probe : ES60WUpdaterDelegate <SPUUserDriver, NSApplicationDelegate>
@property(nonatomic, strong) SPUUpdater *updater;
@end

@implementation Probe
- (void)showUpdatePermissionRequest:(SPUUpdatePermissionRequest *)request
                             reply:(void (^)(SUUpdatePermissionResponse *))reply {
    (void)request;
    reply([[SUUpdatePermissionResponse alloc] initWithAutomaticUpdateChecks:NO sendSystemProfile:NO]);
}
- (void)showUserInitiatedUpdateCheckWithCancellation:(void (^)(void))cancellation { (void)cancellation; event(@"checking"); }
- (void)showUpdateFoundWithAppcastItem:(SUAppcastItem *)item state:(SPUUserUpdateState *)state
                               reply:(void (^)(SPUUserUpdateChoice))reply {
    (void)item; (void)state; event(@"found");
    if ([testMode isEqual:@"cancel"]) { reply(SPUUserUpdateChoiceSkip); finish(@"cancelled"); }
    else reply(SPUUserUpdateChoiceInstall);
}
- (void)showUpdateReleaseNotesWithDownloadData:(SPUDownloadData *)data { (void)data; }
- (void)showUpdateReleaseNotesFailedToDownloadWithError:(NSError *)error { (void)error; }
- (void)showUpdateNotFoundWithError:(NSError *)error acknowledgement:(void (^)(void))acknowledgement {
    (void)error; acknowledgement(); finish(@"no-update");
}
- (void)showUpdaterError:(NSError *)error acknowledgement:(void (^)(void))acknowledgement {
    event([NSString stringWithFormat:@"error:%ld:%@", (long)error.code, error.localizedDescription]);
    event(error.description);
    acknowledgement(); finish([testMode isEqual:@"busy"] ? @"busy-rejected" : @"failed-safely");
}
- (void)showDownloadInitiatedWithCancellation:(void (^)(void))cancellation { (void)cancellation; event(@"downloading"); }
- (void)showDownloadDidReceiveExpectedContentLength:(uint64_t)length { (void)length; }
- (void)showDownloadDidReceiveDataOfLength:(uint64_t)length { (void)length; }
- (void)showDownloadDidStartExtractingUpdate { event(@"extracting"); }
- (void)showExtractionReceivedProgress:(double)progress { (void)progress; }
- (void)showReadyToInstallAndRelaunch:(void (^)(SPUUserUpdateChoice))reply {
    event(@"ready");
    if ([testMode isEqual:@"cancel-ready"]) { reply(SPUUserUpdateChoiceSkip); return; }
    if ([testMode isEqual:@"postpone"]) {
        busy = 1;
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 3 * NSEC_PER_SEC), dispatch_get_main_queue(), ^{
            event(@"idle-again"); busy = 0;
        });
    }
    reply(SPUUserUpdateChoiceInstall);
}
- (void)showInstallingUpdateWithApplicationTerminated:(BOOL)terminated
                           retryTerminatingApplication:(void (^)(void))retry {
    (void)terminated; (void)retry; event(@"installing");
}
- (void)showUpdateInstalledAndRelaunched:(BOOL)relaunched acknowledgement:(void (^)(void))acknowledgement {
    (void)relaunched; acknowledgement(); finish(@"installed");
}
- (void)dismissUpdateInstallation { event(@"dismissed"); }
- (void)updater:(SPUUpdater *)updater didFinishUpdateCycleForUpdateCheck:(SPUUpdateCheck)check error:(NSError *)error {
    (void)updater; (void)check;
    if ([testMode isEqual:@"busy"] && error) finish(@"busy-rejected");
    if ([testMode isEqual:@"cancel-ready"]) {
        // Let the installer acknowledge cancellation before the test app quits.
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, NSEC_PER_SEC), dispatch_get_main_queue(), ^{
            finish(@"cancelled-ready");
        });
    }
}
- (BOOL)updater:(SPUUpdater *)updater shouldPostponeRelaunchForUpdate:(SUAppcastItem *)item
                         untilInvokingBlock:(void (^)(void))handler {
    BOOL postponed = [super updater:updater shouldPostponeRelaunchForUpdate:item untilInvokingBlock:handler];
    if (postponed) event(@"postponed");
    return postponed;
}
- (BOOL)updaterShouldRelaunchApplication:(SPUUpdater *)updater { (void)updater; return YES; }
- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)sender { (void)sender; event(@"terminating"); return NSTerminateNow; }
- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    (void)notification; event(@"started");
    self.canInstall = canInstall;
    busy = [testMode isEqual:@"busy"];
    self.updater = [[SPUUpdater alloc] initWithHostBundle:NSBundle.mainBundle
        applicationBundle:NSBundle.mainBundle userDriver:self delegate:self];
    NSError *error = nil;
    if (![self.updater startUpdater:&error]) { event(error.localizedDescription); finish(@"start-failed"); return; }
    [self.updater checkForUpdates];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 45 * NSEC_PER_SEC), dispatch_get_main_queue(), ^{ finish(@"timeout"); });
}
@end

int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc != 3) return 2;
        resultFile = @(argv[1]); testMode = @(argv[2]); events = [NSMutableArray new];
        if (![NSBundle.mainBundle.bundleIdentifier hasPrefix:@"de.pengusto.naps2.es60w.updatetest."]) return 3;
        [NSUserDefaults.standardUserDefaults removePersistentDomainForName:NSBundle.mainBundle.bundleIdentifier];
        NSApplication *application = NSApplication.sharedApplication;
        [application setActivationPolicy:NSApplicationActivationPolicyAccessory];
        Probe *probe = [Probe new]; application.delegate = probe;
        [application run];
    }
    return 0;
}
