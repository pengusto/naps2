# Upstream synchronization: ES60W 3

The release includes upstream master 4643b6e1cec695f81ed0fa85d197cbf38e321d18,
153 commits after NAPS2 8.5.1's original release snapshot. Existing released
commits/tags are retained by a merge. The only textual merge conflict was two
independent DesktopForm constructor assignments; both are retained.

Mac UI/sidebar, save naming/AutoSave, SDK and generic edge-detection changes
are inherited. The ES60W-specific dark-backing/page-frame path still runs
instead of generic edge detection for the existing USB model match. The
button menu and stop/disposal hooks remain attached. No native helper sources
or proprietary Epson inputs are added or changed by this sync.

The source includes upstream's renamed/reconstructed SVG and PNG artwork.
These retain the upstream source-tree licensing and existing original FatCow
CC attribution/adaptation notices. The older artwork inventory is a dated
baseline, not an exact inventory of the renamed current assets. Full upstream
source and copyright notices accompany this release.

The shipped Mac dependency versions and native graph are unchanged. The optional
ImageSharp backend is absent from the app and from the Mac offline build feed.
Upstream's allowed 3.1.12-to-4.x range is retained for the generic project. The
additional selected upstream unit tests use its 3.1.12 package in an isolated
test cache and report NuGet security advisories. A 4.1.3 test-only trial requires
a separate Six Labors licence and was not bypassed or shipped. This sync does
not claim that the optional generic backend's warnings are repaired.
References: https://github.com/SixLabors/ImageSharp/security/advisories/GHSA-j3p4-wp97-rph4
and https://github.com/SixLabors/ImageSharp/security/advisories/GHSA-j9gm-c75j-xc9q.

The existing 114 notices and 37 supplementary source archives remain applicable
to the shipped Mac dependencies. Licence/source access points to ES60W 3; the
source kit contains the complete current upstream and integration code.

Independent ad-hoc-signed prerelease; no new hardware scan. Existing installed
apps/configurations and the previous downloadable release remain untouched.

A clean-clone check exposed a pre-existing source-package omission: the root
packages/ ignore pattern excluded 43 of the 114 licence texts that were present
in the released app. They are restored from the hash-verified original notices,
explicitly unignored and tracked. The exporter now requires every manifest
licence input in Git, and the builder checks file existence/hashes. No notice
is shortened or replaced by an invented licence.
