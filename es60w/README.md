# NAPS2 ES60W: developer and source guide

The complete NAPS2 8.5.1 application is built with a separate SANE/epsonds helper,
conservative framing, photo-width correction and an opt-in USB button receiver.
See the root README for the DMG and end-user installation. No installer is needed
for the bundled runtime/helper. Paperless is independent and not configured.

## Build from delivered sources

Build prerequisites: Xcode (licence/first launch completed), .NET SDK 10.0.401
and macOS workload 27.0.10722 (workload set **10.0.401.1**), Python 3, CMake, autoconf, automake, libtool and
pkg-config. These are developer requirements, not end-user installers. The root
global.json pins the SDK. Build serially in new output directories outside Git.
Install the exact workload set with `dotnet workload install macos --version 10.0.401.1`;
`10.0.401` alone selects an older macOS SDK requiring Xcode 26.6 instead of 27.0.
Use a dotnet executable whose SDK list includes that exact pin. If `xcode-select -p`
points to Command Line Tools, set `DEVELOPER_DIR` to the licensed full Xcode
developer directory for the build process; do not change the global selection.
An unaccepted Xcode licence is a user action gate, not a reason to skip SDK checks.
The pinned macOS workload also requires Xcode 27.0 specifically. If the local
Xcode has moved to a newer minor version, the `ES60W complete app` PR workflow
builds on the official ARM64 `xcode-27` image with Xcode 27.0 selected. It restores
the verified release-4 dependency feed, builds the full app/helper, and performs
startup/PDF checks with scanner access denied. This workflow only produces
artifacts; release signing/publishing and physical device validation remain separate.

```sh
python3 es60w/build-native.py --downloads /path/to/downloads --output /NEW/native-build
python3 es60w/build-app.py --native-build /NEW/native-build \
  --output /NEW/app-build --dotnet /path/to/dotnet \
  --sparkle-distribution /path/to/Sparkle-2.10.1.tar.xz \
  --updates-config es60w/updates/channel.json
python3 es60w/tools/make-private-dmg.py --app '/NEW/app-build/NAPS2 ES60W.app' \
  --destination '/NEW/dist/NAPS2-ES60W-8.5.1-es60w.4-arm64.dmg' \
  --readme es60w/FIRST-START.de.txt --volume-name 'NAPS2 ES60W'
```

The native builder verifies the three archives in sources.lock.json and applies
the delivered SANE changes. It installs only to its private output prefix.
The macOS libusb configure step forces `ac_cv_func_pipe2=no`: newer SDKs can
weak-link `pipe2` although it is absent on the deployment target (reproduced on
macOS 26.6.2). This selects libusb's existing `pipe`/`fcntl(FD_CLOEXEC)` fallback.
`verification/check-macos-libusb.py` inspects the built library's imports and
rejects `pipe2` before packaging. This static gate must be followed by a real
device-enumeration check on the target macOS before claiming USB readiness;
neither check requires a paper feed.
The app builder builds SimpleBase from the delivered preferred C# sources first,
then performs the full macOS/static Objective-C registrar build, never a DLL
swap. One worker, no shared compilation or buildservers; a neutral temporary
source root keeps personal build paths out of the app. No scan is part of a build.

For a cold-cache build from the delivered source kit, add
`--nuget-source /path/to/package-inputs/nuget-feed --nuget-packages /NEW/package-cache`
to build-app.py. The source-built SimpleBase feed is created automatically.
NuGet build inputs and declared third-party snapshots are in the main source kit;
the separate third-party source archive supplies the additional pinned native
submodules, PDFium graph, runtime and historically version-matched sources.

The helper runs in a separate process through CLI/TIFF. Only epsonds is bundled
as its backend. Offline replay utilities and synthetic scan substitutes do not
belong in the shipped app. App startup does not scan or enable USB listening;
the button receiver is an explicit per-session opt-in.

## Verification and distribution

See verification/ for earlier software evidence and legal/release-assessment-2026-10-25.md
for the current publication decision and its limits. New binary versions receive
full app/worker startup, dependency and offline PDF checks. Hardware tests from
older builds are not silently attributed to a new binary.

The app is ad-hoc signed, without Developer ID or notarization. The documented
Apple first-launch confirmation remains necessary on a downloaded copy. There
is no Gatekeeper-disable script. Current supported scope is USB ES-60W, arm64,
metadata minimum macOS 14; software host 26.6.2. Existing installations and
settings are not touched by build/package tools.

prepare-local-release.py exports the committed clean source snapshot, matching
native inputs, build packages, separate additional source download, patch series
and SHA256SUMS. It performs no Git push or upload. Replay its patch series with
`git am --keep-cr` to preserve the original CRLF licence readme bytes.

## Licences and source provenance

The GPL-2.0-only unused NAPS2.Sane.Binaries placeholder is removed from the Mac
project. The main application uses upstream's GPLv3 option; the separate SANE
program retains GPLv2, and other components retain their own notices. The local
About link exposes licence texts, attributions and the matching source release.
The orchestration tools have LICENSE-tools.txt; vendored library code keeps its
original licence. SOURCE-STATUS.json distinguishes source evidence from claims
of independent binary reproduction. Historical research reports are retained
as dated evidence and superseded where the release assessment says so.

Never import private reverse-engineering history, Epson binaries/resources,
decompiled Epson code, real scan images or user credentials into this fork.

## Upstream sync in ES60W 3

This branch includes upstream master 4643b6e1cec695f81ed0fa85d197cbf38e321d18
(153 commits after the original release base). Published history is merged,
not rebased; release es60w-v8.5.1-2 remains intact. The source exporter emits a
clean integration patch commit against the recorded current upstream base,
whose tree equals the release snapshot. That patch is a source reconstruction
aid, not a rewrite of the public branch. Apply it with git am --keep-cr.

The native scan helper, automatic width/length logic and button receiver remain
from the previous ES60W integration. App/worker, PDF/AutoSave replay, framing
and button simulations are checked without a real device. No new physical
scan validation or notarization is claimed.

ES60W 4 adds signed complete-app updates, including the same SANE runtime as ES60W 3. See [update build/signing/source instructions](updates/README.md). The source kit includes both Sparkle archives from updates/sparkle.lock.json. No new physical scan was performed.
