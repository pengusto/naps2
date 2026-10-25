# Distribution licence selection

The NAPS2 application code is distributed under GPL version 3 using upstream's
GPL-2.0-or-later option. Original copyright notices and licence texts remain.
This does not relicense third-party code, independent artwork, provider marks,
or the separate SANE scanimage program.

The external scanimage/epsonds program remains GPL version 2. It exchanges
ordinary CLI arguments and TIFF with the application. The GPL-2.0-only
NAPS2.Sane.Binaries placeholder package has been removed from the Mac application
project; no direct SANE native collection is included in the GUI process.
The free helper is retained, with its complete modified preferred sources.

Permissive libraries retain their MIT, BSD, Apache or other actual notices.
Apache-2.0 code can be included under the GPLv3 application choice; it must not
be silently combined into a GPLv2-only application.
https://www.apache.org/licenses/GPL-compatibility.html

Identified FatCow artwork retains CC BY 3.0 US, attribution and change notices;
it is not relabelled GPL. Provider marks are not licensed by the application
licence. See ARTWORK-NOTICES.md and the distinct source/release status.

The supplied standard .NET interpreter/runtime and Apple system frameworks are
analysed as standard runtime/system components under GPLv3 section 1. No blanket
exception is claimed for PDFium, JPEG, third-party application libraries or
arbitrary Microsoft packages. Exact .NET and macOS binding source revisions are
preserved as additional evidence anyway. Xcode, SDKs, compilers, CMake and
unmodified general build tools remain documented prerequisites.
https://www.gnu.org/licenses/gpl.en.html#section1

The source download must remain available beside the exact binary version.
Matching source and build instructions are required; byte-identical binary
reproduction is a different claim. The release provides the matching source downloads alongside its binary; retain
all parts of that download set when redistributing this package.
https://www.gnu.org/licenses/gpl-faq.en.html#MustSourceBuildToMatchExactHashOfBinary
