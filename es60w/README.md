# NAPS2 ES60W — local release preparation

This branch contains the full NAPS2 8.5.1 application plus the independent
SANE/epsonds helper integration, conservative framing, photo-width correction,
and opt-in USB scanner-button receiver. It is a local preparation branch for
`pengusto/naps2`; no release or push is performed by these tools.

The intended installation is one DMG: drag **NAPS2 ES60W.app** to Applications,
open it, and scan a single USB ES-60W. The app bundles .NET, scanimage, epsonds,
libusb and libjpeg. End users need no Epson, Homebrew or .NET installation.
300 dpi RGB, automatic framing and one PDF per scan in `Documents/Scans` are
preset. Scanner-button listening must be enabled in the Scan menu each session.
Paperless is independent and is not configured by this package.

Only macOS arm64 is built. The metadata minimum is macOS 14; software checks
are performed on macOS 26.6.2. No universal Epson support, WLAN support, perfect
physical edge measurements or new hardware validation is claimed.

## Build locally

Build prerequisites: Xcode with its licence/first launch completed, .NET SDK
10.0.401 and macOS workload 27.0.10722, Python 3, CMake, autoconf, automake,
libtool and pkg-config. These are build requirements, not end-user installers.
Use the exact pinned source archives in `sources.lock.json` in a download
directory. Every archive is checked before use; missing archives are downloaded
only from their recorded upstream URL. Builds are serial and never install
systemwide. Use new output directories outside the source checkout.

```sh
python3 es60w/build-native.py --downloads /path/to/downloads --output /path/to/native-build
python3 es60w/build-app.py --native-build /path/to/native-build \
  --output /path/to/app-build --dotnet /path/to/dotnet
python3 es60w/tools/make-private-dmg.py --app '/path/to/app-build/NAPS2 ES60W.app' \
  --destination '/path/to/dist/NAPS2-ES60W-8.5.1-es60w.1-arm64.dmg' \
  --readme es60w/FIRST-START.de.txt --volume-name 'NAPS2 ES60W'
```

The second command performs the full macOS build including its static registrar;
it does not replace a DLL in an old app. Native dependencies use their matching
source-built headers. The helper is a separate CLI program and does not load
SANE libraries into the GUI/worker process. The shipped native backend is epsonds
only; offline replay tools and synthetic fixtures do not belong in the app.

`SOURCE-STATUS.json` distinguishes preferred application/helper sources from
the still-open final corresponding-source review of other third-party native
and managed inputs. Included licence texts are not a claim that every dependency
has been independently rebuilt. Preserve the upstream GPL/LGPL and component
notices; our separate orchestration tools are under `LICENSE-tools.txt`.

## Distribution status

The local DMG is ad-hoc signed, not Developer-ID signed or Apple-notarized.
Gatekeeper remains enabled; normal quarantined Finder first launch is not
certified. Final third-party source closure, artwork grants, trusted signing,
notarization and final target-Mac startup remain public-release work.

Existing installed apps and user settings must not be overwritten by these
tools. No device command, real scan, Paperless upload, Git push or GitHub release
is part of this preparation. Keep the private reverse-engineering repository
and its history separate from this clean NAPS2 branch.

For a cold-cache rebuild from the delivered source kit, add
`--nuget-source /path/to/package-inputs/nuget-feed --nuget-packages /NEW/package-cache`
to `build-app.py`. The feed contains the resolved project packages plus the
runtime/targeting downloads pinned in `framework-downloads.lock.json`. SDK and
Xcode/workload prerequisites still need to be installed on a build machine.
The root `global.json` pins the SDK; it is not an end-user runtime installer.
