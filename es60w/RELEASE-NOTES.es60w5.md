# NAPS2 ES60W 5 – macOS USB startup fix

Fixes a crash in the bundled free scan helper during USB device discovery on
macOS 26.6.2. A newer Apple SDK made `pipe2` linkable even though the target
system did not provide it. The macOS build now uses libusb's existing
`pipe`/`fcntl` fallback, retaining its descriptor flags and error handling.
A build gate rejects a `pipe2` import before packaging.

The pinned SANE/epsonds, libusb and JPEG source versions and scan/framing
algorithms are unchanged. No system-wide scanner driver is installed or removed.
Epson software can remain installed; quit competing scanner applications and
button listeners before using the free USB helper if the interface is busy.

Validation distinguishes device enumeration and physical scanning of the local
repair from checks of the final release artifact. A local repair of ES60W 4
completed one USB scan at 300 dpi in colour, with local PDF and lossless PNG
export. No private test image is included in sources, this PR or release assets.
Final package checks and their scope are recorded in the release evidence.
This is not a claim of Epson-identical quality, exact paper dimensions or
validation on another Mac.
In the three single-feed comparisons, the local repaired helper retained a thin
dark border and clipped the upper decorative petal on the small test card;
ScanSmart retained that detail. This existing framing limitation is not corrected
by the startup-only fix and remains follow-up work.

Download the single arm64 DMG, which includes the complete app and helper.
Keep existing working apps and settings. The signed update channel replaces the
complete application only after confirmation. The app remains ad-hoc signed,
without Apple Developer ID/notarization; keep Gatekeeper enabled and use Apple's
per-app first-launch approval if needed. No Paperless upload is configured.
