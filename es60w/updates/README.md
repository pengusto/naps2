# Complete-app update channel (local preparation)

The ES60W fork updates the whole application, including its pinned, patched
SANE/epsonds helper. It does not install system-wide drivers or download an
arbitrary new backend into an older app. This preserves the tested interface,
framing and button integration. A newer SANE version must be integrated and
validated before shipping it in a new app bundle. The SANE MR is independent.

This branch is **local and unpublished**. The channel URL in channel.json is
reserved for a future release asset and is not live. Automatic checks default
off; users can enable them in the application menu. Installation always needs
confirmation. Appcast and complete update archives require Ed25519 signatures;
archives are verified before extraction. No telemetry/system profile is sent.
The normal NAPS2 Windows updater is not used. Existing releases through ES60W 3
have no updater: users must install an updater-enabled DMG once to bootstrap.

## Implementation

Sparkle 2.10.1 provides the native update UI, version comparison, signature
validation, download, staging and installation. A small Objective-C bridge is
loaded only in the ES60W desktop app when the package marker is present. Workers,
CLI and upstream builds do not start an updater. Normal NAPS2 closing prompts
remain; a busy/unsaved-page guard prevents checking and defers relaunch if a new
operation or unsaved page appears during download. Users may finish/save their
work before the pending installation resumes.

No update installer or extractor is implemented in C# or shell. The wrapper is
compiled from UpdaterBridge.m. UpdateProbe.m is an automated test user driver
and must never be packaged. Tests verify that it is absent from the real app.

The distribution archive and preferred source archive are pinned in
sparkle.lock.json. Fetch them to a build-input directory outside Git and check
the recorded SHA-256 values. Only the framework is embedded, with its symlinks
and permissions preserved. Its upstream signature is verified before staging.
Embedding re-signs the framework and its nested tools inside out for this
ad-hoc host, preserving XPC entitlements. Sparkle installer peers cannot retain
an unrelated signing identity. Do not sign with `codesign --deep`; `--deep` is
used only for verification. Bundled upstream licence notices are retained.

## Local build and checks

Use the standard es60w/build-app.py prerequisites and serial build. Add:

```sh
--sparkle-distribution /build-inputs/Sparkle-2.10.1.tar.xz \
--updates-config es60w/updates/channel.json
```

Both flags are optional together; omitting them preserves the existing package
path. Invalid channel configuration/archive hashes fail before the .NET build.
This preview has build number 851004 and release label 8.5.1-es60w.4-local. It is
not installed by the build scripts. App/worker and PDF checks use the existing
software-only scripts in es60w/tools.

```sh
python3 es60w/updates/check-updates.py \
  --app '/new-build/NAPS2 ES60W.app' \
  --sparkle /build-inputs/sparkle \
  --output /private/tmp/NEW-es60w-update-check
```

This compiles a separate test probe, creates a disposable private test key
outside Git, and serves signed test archives only at 127.0.0.1 on a random port.
It changes only disposable app copies with a dedicated test bundle identifier.
Full replacement is checked by comparing every file of the installed copy to
the payload, including a changed marker inside the complete SANE helper bundle.
The original input app is not modified. Installer fixtures must be in
/private/tmp: an independent installer process can be delayed by macOS folder
privacy controls when asked to replace a test app inside Documents/Desktop.
The tool rejects that location rather than reporting an uncompleted install as
successful. A generic installer-launch error cannot pass a signature test.

Feed/version/early-cancel probes deny IOKit, installed apps/settings, helper
execution and outbound IP except loopback. Archive-signature, full-install and install-cancel probes cannot use
sandbox-exec: launchd rejects installer registration from that wrapper. They
run only the test executable (which has no scanner API), with fresh settings.
Both old and new fixtures use that probe as their main executable; a relaunch
without test arguments exits immediately. The real NAPS2 binary is retained
and can be checked separately as a worker. Do not claim
these installer subprocesses inherit the negative-probe sandbox. Follow the
check with normal sandboxed worker/PDF checks of the resulting real app.

## Signing and future publication

The release key was generated locally in the login Keychain, account
`de.pengusto.naps2.es60w.updates`. channel.json contains only its public key.
No private release key is exported into Git or build outputs. The first access
by Sparkle's signing tools can require a user Keychain confirmation. Offline
tests use a different disposable key and do not require that access.
Preserve/back up the release key through a secure Keychain backup before
depending on it for published updates.

Prepare a full-app zip and signed feed without uploading:

```sh
python3 es60w/updates/prepare-update.py \
  --app '/new-build/NAPS2 ES60W.app' \
  --sparkle-tools /build-inputs/sparkle/bin \
  --output /NEW/update-assets \
  --download-url-prefix https://github.com/pengusto/naps2/releases/download/NEW-RELEASE/
```

Before publication, choose the real release version/build number, update the
matching source-release/About links, export the full matching source kit with
the Sparkle archive/source pins and notices, and check the complete app and
DMG. The existing ES60W-3 source exporter deliberately rejects this preview;
extend its version/source-input handling before preparing the real new release.
Publish that complete release first. Then publish the signed appcast.xml
as an asset of the dedicated `es60w-updates` prerelease, retaining the permanent
feed URL. Test downloaded URLs and signatures before enabling automatic checks
by default. Do not modify a signed appcast after signing it. No publishing or
automatic background release job is added by this branch.

Ed25519 update signing does not replace Apple Developer ID/notarization. This
preview remains ad-hoc signed; the initial downloaded DMG may still require
Apple's normal first-launch confirmation. No Gatekeeper settings are changed.
