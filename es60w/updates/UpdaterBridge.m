// Copyright (c) 2026 Pengusto. MIT; see ../LICENSE-tools.txt.
// Sparkle owns download verification, extraction, installation and replacement.
#import <Cocoa/Cocoa.h>
#import <Sparkle/Sparkle.h>

typedef int (*ES60WCanInstall)(void);

@interface ES60WUpdaterDelegate : NSObject <SPUUpdaterDelegate>
@property(nonatomic) ES60WCanInstall canInstall;
@property(nonatomic, copy) void (^pendingInstall)(void);
@property(nonatomic, strong) NSTimer *timer;
@end

@implementation ES60WUpdaterDelegate
- (BOOL)updater:(SPUUpdater *)updater mayPerformUpdateCheck:(SPUUpdateCheck)check
         error:(NSError * __autoreleasing *)error
{
    (void)updater; (void)check;
    if (self.canInstall && self.canInstall()) return YES;
    if (error) *error = [NSError errorWithDomain:@"de.pengusto.naps2.es60w.updates" code:1
        userInfo:@{NSLocalizedDescriptionKey:
            @"Bitte laufende Vorgänge beenden und ungespeicherte Seiten sichern, bevor du aktualisierst."}];
    return NO;
}
- (BOOL)updater:(SPUUpdater *)updater shouldPostponeRelaunchForUpdate:(SUAppcastItem *)item
                         untilInvokingBlock:(void (^)(void))installHandler
{
    (void)updater; (void)item;
    if (self.canInstall && self.canInstall()) return NO;
    self.pendingInstall = installHandler;
    // A scan/import/save may have started during the download. Defer on the
    // main run loop; never poll the scanner and never force termination.
    __weak ES60WUpdaterDelegate *weakSelf = self;
    self.timer = [NSTimer scheduledTimerWithTimeInterval:1 repeats:YES block:^(NSTimer *timer) {
        ES60WUpdaterDelegate *owner = weakSelf;
        if (!owner) { [timer invalidate]; return; }
        if (owner.canInstall && owner.canInstall()) {
            void (^resume)(void) = owner.pendingInstall;
            owner.pendingInstall = nil;
            [timer invalidate]; owner.timer = nil;
            if (resume) resume();
        }
    }];
    return YES;
}
@end

static SPUStandardUpdaterController *controller;
static ES60WUpdaterDelegate *updateDelegate;

// All entry points are called on the macOS main thread by the Eto desktop form.
int es60w_update_start(ES60WCanInstall canInstall)
{
    if (![NSThread isMainThread] || !canInstall) return 0;
    if (controller) return 1;
    updateDelegate = [ES60WUpdaterDelegate new];
    updateDelegate.canInstall = canInstall;
    controller = [[SPUStandardUpdaterController alloc] initWithStartingUpdater:NO
        updaterDelegate:updateDelegate userDriverDelegate:nil];
    [controller.updater clearFeedURLFromUserDefaults];
    NSError *error = nil;
    if (![controller.updater startUpdater:&error]) {
        NSLog(@"ES60W updater could not start: %@", error.localizedDescription);
        controller = nil; updateDelegate = nil;
        return 0;
    }
    return 1;
}

int es60w_update_state(void)
{
    if (![NSThread isMainThread] || !controller) return 0;
    return 1 | (controller.updater.canCheckForUpdates ? 2 : 0)
        | (controller.updater.automaticallyChecksForUpdates ? 4 : 0);
}

void es60w_update_check(void)
{
    if ([NSThread isMainThread] && controller.updater.canCheckForUpdates)
        [controller checkForUpdates:nil];
}

void es60w_update_automatic_checks(int enabled)
{
    if ([NSThread isMainThread] && controller)
        controller.updater.automaticallyChecksForUpdates = enabled != 0;
}

void es60w_update_stop(void)
{
    if (![NSThread isMainThread]) return;
    updateDelegate.canInstall = NULL;
    [updateDelegate.timer invalidate];
    updateDelegate.timer = nil; updateDelegate.pendingInstall = nil;
    // Keep Sparkle alive through normal application termination. Its installer
    // may be handling an explicitly approved install-on-quit operation.
}
