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

The legal-input check rejects the obsolete direct-SANE placeholder, verifies every notice against the packaged file, and checks every supplemental source archive. Build scripts whose names contain `deps` must not be classified as licence texts: only notice/licence content belongs under `licenses/`; original build scripts stay in the source archives.

Preserved vendor notices may use CRLF. Replay the exported mbox with `git am --keep-cr`: Git's default mail parser otherwise normalizes an original notice and breaks the exact source-tree/hash proof. Keep the notice bytes unchanged; prefer the full source archive as the primary source payload.


## ES-60W framing regression, 26 October 2026

A width-only fallback retained a skewed bottom/right backing border when one
side of a small page met the acquisition boundary. The refinement first keeps
that established width decision, then fits the connected light-paper surface.
An observed vertical and horizontal edge must agree on a small rotation.
Unobserved acquisition edges are not invented. The output canvas encloses the
complete detected paper envelope, with bilinear sampling and an outward margin;
only confidently fitted exterior edges can be filled white. The transform and
its optional bounds are undoable and serialized with the untouched source.
Ambiguous light coverage, inconsistent edges, dark/photographic pages, exterior
light/saturated marks and detected near-edge print retain the old conservative
path. This is specialized light-paper framing, not general photo segmentation.

The native portable `page-frame-check` now checks 251 cases, including known
printed marks near all four edges, positive/negative skew, inverted buffers,
recovery XML and a closed printed rectangle that must not become a paper crop.
The Linux CI job runs this executable; it has no scanner code or hardware access.

Private saved scans were evaluated locally by the same compiled image operations:
no helper or scanner was invoked. In manually inspected content rectangles, all
58,227 (second scan) and 58,013 (first scan) pixels below RGB mean 180 remained
inside the output and outside all backing-fill predicates in the initial check.
Final counts/geometry are in the local evaluation report, not private source
fixtures. This is a geometric retention check on those selected regions, not a
proof of semantic completeness on arbitrary documents. The first source already
clipped an upper motif: processing cannot recover content absent from the source.
A residual seam is preferable to extending an uncertain crop into content.

Lesson: a passing source build and synthetic bounds check alone do not prove a
clean delivered scan. Keep a visual before/after and check the actual transform's
fill predicates, as well as its output bounds, against source content.


## Large-angle offline refinement, 26 October 2026

The skew stress test exposed a scope gap: the previous side/row fit only covered
about ±2.9°, while a saved scan was about 30° off-axis. Do not widen that fit's
slope threshold alone: its row extrema switch between different physical edges.
The new path fits a minimum-area rectangle to the convex envelope of the largest
connected light-paper surface, verifies substantial support on three sides and
both perpendicular axes, and encloses all observed paper before rotation. The
existing sampler fills only outside that complete paper envelope. It does not
apply an inscribed crop or change colours, scale or perspective.

The restricted candidate range is 3–40° relative to the nearest acquisition axis;
±15/30/39° cases are tested, including a corner clipped by acquisition. It is not
a general guarantee for all angles, dark artwork, perspective or damaged paper.
Few isolated bright/coloured exterior components below 16 pixels are treated as
scanner dust, with a strict total-area bound; substantial disconnected exterior
marks, printed frames, inconsistent edges and insufficient dark backing reject
the new path. Dust classification is a heuristic, not semantic content knowledge.
Original data and undo/recovery remain intact. Absent source corners cannot be
recovered. The previous small-angle/fallback paths are preserved.

329 portable checks pass, with known print close to all four corners, ±39° skew,
RGB/BGRA/RGBn and inverted source/output rows, acquisition clipping, printed-frame,
triangle/dark/white-backing counterexamples, exterior marks, and XML recovery.
The private raw scan was processed by that same compiled C# operation without
scanner code. In a manually specified and visually inspected source content
region, 58,339 dark candidate pixels were checked against both output bounds and
all exterior-fill predicates; none were excluded. This regional geometric check
is not a universal semantic proof or pixel-identity claim after interpolation.
Private before/after images remain outside Git. Local source PNG hash matched the
pre-existing scan archive checksum. Public evidence is in
`large-angle-2026-10-26.json` and includes no scan image or machine-specific path.


## Exterior seam refinement, 26 October 2026

Extreme convex-hull pixels retained a black seam after large-angle rotation.
Long supported edge segments now refine their offset with the median of nearby
observed light transitions (excluding acquisition-clipped endpoints). Only a
supported edge receives a one-source-pixel transition cleanup. The enclosing
canvas and observed full-paper envelope are unchanged. An interior dark-print
band near a proposed cleaned boundary cancels the refinement and restores the
previous conservative fill bounds. This is a threshold/geometry heuristic, not
semantic proof of paper versus borderless ink; incomplete acquisition corners
remain uncertain and can retain a small seam. Do not erase arbitrary dark pixels.

401 tests pass: the large-angle corner/edge marks now exercise 2- and 5-pixel
insets, in addition to all previous ambiguity and recovery cases. On the same
private saved raw scan, all 58,339 controlled content candidates remain within
output and outside every fill predicate; source checksum unchanged. The number
of pixels below mean RGB 140 in the outer 15-pixel output band falls from 6,166
to 222 (96.4%); this is a seam metric for this example, not quality equivalence.
Some dark pixels remain near acquisition-clipped corners. The right response is
to retain those uncertain areas rather than claim total border removal or shrink
the whole page. No scan images or machine paths are committed.


### Interpolation boundary follow-up

The renderer previously checked only each destination pixel centre against the
paper mask, then interpolated four unmasked source neighbours. A black exterior
neighbour could reintroduce a dark fringe. Each neighbour now uses the same
confirmed paper bounds; no new segmentation, inward crop or wider threshold is
introduced. A dedicated all-white-paper/black-exterior regression asserts that
no dark interpolation sample crosses the mask. The original 401 cases remain.
On the saved stress scan, dark outer-band candidates drop only from 222 to 212;
the complete region more than 15 output pixels from the edge is byte-identical
to the prior output. Residual clipped-corner seams are not claimed solved.
Further deletion would require additional reliable paper evidence; dark ink at
a physical edge can be indistinguishable from backing. Keep source/recovery.
