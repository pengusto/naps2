# Independent prerelease assessment, 25 October 2026

This record supersedes the publication-pending conclusions of the earlier dated
local research reports; it preserves their observations and evidence. It is a
technical source/licence assessment for this exact fork, not a legal guarantee.
The target is an independent, ad-hoc-signed prerelease with complete source
artifacts. Notarization and perfect reproduction of every permissive binary are
not claimed as accomplished and are not relabelled copyright permissions.

## Concrete changes since the local draft

- Removed the unused GPL-2.0-only direct-SANE NuGet placeholder from the Mac app;
  the independent CLI helper remains, with full modified preferred sources.
- Replaced the historical SimpleBase NuGet input with our explicitly versioned
  source build (1.3.2-es60w.1) from the delivered, unmodified upstream preferred
  sources. Assembly ABI 1.3.1.0 retained; no claim that its old NuGet binary was
  produced from that commit. The build creates this package before restoring
  the app, including when using the offline source kit.
- Completed the targeted PDFium graph comparison: its pinned minimal macOS
  recipe disables V8/XFA/PartitionAlloc, defaults to AGG and disables Fontations.
  HarfBuzz is an unconditional core/fpdfapi/edit dependency and is now archived
  at its exact DEPS pin with its licence. Brotli is also captured conservatively.
  Fifteen selected PDFium dependency archives plus exact source and recipe are
  delivered. Disabled optional/test targets are not treated as shipped code.
- The runtime/macOS binding revisions, wrapper source/submodule pins, library
  notices, build inputs and additional source archives are delivered with hashes.
  Older MIT/Apache packages with only an official matching version/tag retain
  that evidence level; it is not falsely promoted to a declared NuGet commit.
  An independent rebuild of every permissive package is not asserted.
- FatCow's specific CC BY 3.0 US grant accompanying the original package is the
  basis for identified icons. Original grant, attribution and adaptation notes
  accompany the app; generic original-site wording is preserved in research.
  Other unchanged UI/branding assets are inherited from the GPL NAPS2 source;
  no contrary per-file restriction was identified in it. Remaining individual
  artist attribution is incomplete, not fabricated. Provider marks identify
  existing integrations; independent fork wording avoids claiming endorsement.
  No proprietary Epson assets or decompiled implementations are shipped.
- Full editable LGPL project sources and rebuild instructions are supplied. The
  bundle uses an ad-hoc signature and no protected signing secret; users can
  rebuild/repackage and ad-hoc re-sign modified libraries with the supplied tools.
  The earlier local replacement/re-sign check remains dated evidence, not a
  claim that a modified library can be substituted in a fixed registrar blindly.

## Source delivery

The DMG, complete app/native source kit, separate third-party sources, patch
series and SHA256SUMS belong to the same version. Source snapshots, licence
notices and build recipes are provided, rather than an unbounded future promise.
The main application selects GPLv3 under upstream GPL-2.0-or-later; the separate
SANE program retains GPLv2. Component notices/alternative grants remain intact.

Primary references: [NAPS2 licence](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/LICENSE),
[ASF GPL compatibility](https://www.apache.org/licenses/GPL-compatibility.html),
[GNU source versus byte-identical rebuild](https://www.gnu.org/licenses/gpl-faq.en.html#MustSourceBuildToMatchExactHashOfBinary),
[PDFium DEPS](https://pdfium.googlesource.com/pdfium/+/d3e62278db7489af9e0b686835d1c8aca218c3d7/DEPS),
[pinned build recipe](https://github.com/bblanchon/pdfium-binaries/blob/a068e5317bb780d0afdf00d8b341938d9f36d2fe/steps/05-configure.sh).

## Limits kept visible to users

Ad-hoc signing is not Developer ID/notarization. Apple documents its one-time
[Open Anyway flow](https://support.apple.com/en-us/102445); no command disabling
Gatekeeper is included. A quarantined Finder launch on the target Mac remains
untested. macOS minimum metadata 14.0, software host 26.6.2, arm64 USB ES-60W only.
The release dependency/package rebuild gets no new physical scan. Conservative
framing can retain a thin border; exact millimetres/Epson parity are not claimed.
The working installed app/configs and private REA history remain separate.
