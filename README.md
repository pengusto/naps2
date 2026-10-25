# NAPS2 ES60W for macOS

**One app for a USB Epson ES-60W on an Apple Silicon Mac.** Independent NAPS2 fork with a bundled free SANE/epsonds scan helper. No separate Epson software, Homebrew or .NET installation is needed for scanning.

**[Download the DMG](https://github.com/pengusto/naps2/releases/download/es60w-v8.5.1-3/NAPS2-ES60W-8.5.1-es60w.3-arm64.dmg)** · [All release files, sources and SHA-256 checksums](https://github.com/pengusto/naps2/releases/tag/es60w-v8.5.1-3) · [Deutsch: Installation](es60w/INSTALL.de.md)

1. Open the DMG and drag **NAPS2 ES60W.app** to Applications. Keep another working copy under its existing name or location; do not overwrite it.
2. Open the app. This prerelease is **ad-hoc signed and not Apple-notarized**. If macOS blocks it, first try to open it, then use **System Settings → Privacy & Security → Open Anyway**. [Apple's instructions](https://support.apple.com/en-us/102445). Leave Gatekeeper enabled.
3. Connect the ES-60W by USB, insert a sheet and click **Scan**. The preset is colour, 300 dpi and automatic framing. Each new scan saves a PDF in **Documents/Scans**.

The physical scanner button is optional: enable its listener in the Scan menu each session and keep the app running. Paperless is a separate optional destination; this download has no Paperless account or automatic upload configured.

The source branch includes the 153 upstream commits through
[`4643b6e`](https://github.com/cyanfish/naps2/commit/4643b6e1cec695f81ed0fa85d197cbf38e321d18).
This is a snapshot of upstream master after the official 8.5.1 release, with our
ES60W integration retained. [Previous ES60W release](https://github.com/pengusto/naps2/releases/tag/es60w-v8.5.1-2) remains available.

## Supported scope

- Apple Silicon (arm64), one **ES-60W via USB**. Intel Macs, Wi-Fi and other Epson models are not validated by this fork.
- macOS minimum in the bundle: 14.0. Software checks ran on 26.6.2; other macOS versions and first launch on a different Mac remain untested.
- Earlier builds were tested with the physical ES-60W. This release integrates upstream Mac UI, saving and SDK changes and has **not received a new physical scan test**. It is a prerelease, with conservative framing: a small residual dark border can remain. Exact millimetre accuracy and Epson-identical cropping are not claimed.
- No background Epson service is needed. The app bundles its runtime and a separate free helper. No proprietary Epson driver, resources, decompiled implementation, private documents or credentials are included.

## Sources, licences and contributions

[Build instructions and architecture](es60w/README.md) · [Release assessment](es60w/legal/release-assessment-2026-10-25.md) · [Licences](es60w/licenses/DISTRIBUTION-LICENSE.md) · [Artwork credits](es60w/licenses/ARTWORK-NOTICES.md)

The release contains the complete editable fork source, native source archives, NuGet build inputs, additional third-party source snapshots, patch series and checksums. These source downloads are for developers; **users only need the DMG**. The app's About dialog links to local component notices and the source release.

This is maintained separately while focused upstream changes are reviewed: [NAPS2 PR #938](https://github.com/cyanfish/naps2/pull/938) and [SANE MR !1061](https://gitlab.com/sane-project/backends/-/merge_requests/1061). Those contributions cover parts of the integration; accepting them alone does not ship this complete macOS app.

NAPS2 and Epson are their respective owners' names. This fork is not an official release or an endorsement by either project or Epson. Original copyright and component notices remain. Main application code is distributed under GPLv3 using upstream's GPL-2.0-or-later option; the separate SANE helper retains its own licence.

For the original cross-platform application, see [NAPS2](https://github.com/cyanfish/naps2) and the [upstream README](es60w/UPSTREAM-README.md).

[Local update-channel preparation](es60w/updates/README.md): unpublished complete-app updates, including the pinned SANE helper. Existing public downloads are unchanged.
