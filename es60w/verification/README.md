# Offline release verification

No new physical scan or device command belongs in release preparation.
Installed working apps/configuration remain unchanged and are checked by file
hashes before and after this work. Do not enable scanner-button listening in
software tests. Use only `--self-test` on the real receiver; USB lifecycle tests
link an explicitly fake API with no libusb imports.

The complete application must finish its macOS/static-registrar build and print
the final `Build succeeded.` summary. A DLL replacement or partially generated
bundle is insufficient. Build tools check transitive launcher C inputs before
the registrar build, so missing local includes fail early.

On macOS, do not apply a blanket `(deny network*)` rule to the .NET build:
MSBuild's out-of-process task host needs local Unix-domain communication. One
observed restricted run failed with MSB4216/MSB4027; the same source built after
restricting IP traffic while retaining local IPC. Keep IOKit denied and block
Epson files and installed application/configuration writes. Never weaken
Gatekeeper or change a working installation to fix a build sandbox problem.

Checks supplied in `../tools/` cover fresh-HOME GUI/worker start, static native
links, synthetic PNG import/PDF export, and an AutoSaver replay with a disposable
fake scanimage. The latter is a file fixture, not a physical scan. Dependencies
for that check are Python Pillow/pypdf and clang; no fixture belongs in the DMG.

`page-frame-check/` verifies the actual built image operations against generated
RGB/BGR/RGBA/BGRA/RGBn buffers, row inversion and conservative fallback cases.
Build it serially with `-p:Naps2Source=/path/to/checkout`; never write private
scans into this source branch or its delivered source kit.

Developer-ID signing/notarization and a quarantined Finder first launch are
separate from these software checks. Passing a synthetic test does not establish
new physical dimensions, Epson equivalence or target-Mac USB behavior.

The Apple trimmer was observed retaining CodeView PDB paths despite symbol-removal properties. The build therefore copies sources to a neutral `/private/tmp/naps2-es60w-build-*` directory. It removes external native RPATHs during packaging and fails if the builder's home path remains in any output file. Managed assemblies are not binary-patched. Generated build roots are recorded outside the app and may be removed after verification.
