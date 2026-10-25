# Drittquellen- und Grafikrechte: gezielte lokale Prüfung, 25.10.2026

**Ergebnis:** Wesentliche konkrete Nachweislücken sind geschlossen und eine
unnötige Lizenzkonstellation ist aus dem Mac-Projekt entfernt. Der öffentliche
Release ist weiterhin **nicht vollständig geklärt**. Die verbleibenden Punkte
stehen unten mit konkreter Datei-/Komponentenzuordnung; kein pauschales
„alle Rechte erledigt“ und keine neue Hardwareabnahme.

## Tatsächlich ausgelieferter Umfang

Ausgangspunkt ist das lokale Paket 8.5.1-es60w.1 und Quellhead
`efa99563f478d4776282421d76616e73a938d2f2`. Die Prüfung verbindet tatsächliche
App-DLLs, aufgelöste Runtime-Assets, NuSpec-Metadaten und einen eigenen statischen
PE-Metadatenleser. Sie lädt oder führt Bibliothekscode nicht aus. Von den 89
aufbewahrten Buildpaketen entsprechen 33 Paketgruppen dem ursprünglichen
verwalteten Bundle; weitere acht Gruppen stammen aus den eigenen NAPS2-Projekten.
94 weitere DLLs sind Runtime-/Plattformbestandteile. Ein Build-Input allein wird
nicht als ausgelieferte App-Komponente eingestuft.

Die unbenutzte `NAPS2.Sane.Binaries.dll` war tatsächlich im Bundle vorhanden.
Ihr Paket 1.2.3 erklärt GPL-2.0-only. Die alte direkte SANE-Sammlung war bereits
entfernt, aber diese Referenz verblieben. Im lokalen Mac-Projekt ist jetzt auch
die unnötige Paketreferenz entfernt: Kontrollbuild mit 32 Paketgruppen und 134
statt 135 DLLs; der separate SANE-Helfer bleibt erhalten. Keine Regel zur
Neu-Lizenzierung von GPL-2.0-only erfunden. [Primäre Paketquelle](https://github.com/cyanfish/naps2-sane/blob/e620b173d5ac9efdadfa723b5c80ac4aa16fe086/NAPS2.Sane.Binaries/NAPS2.Sane.Binaries.csproj).

## Geklärte Lizenzzuordnung und gesicherte Quellen

| Teil | Nachweis / Umsetzung | Präzise Grenze |
|---|---|---|
| NAPS2-Code | Upstream GPL-2.0-or-later; für diesen App-Code GPLv3 gewählt, Originaltexte erhalten. Die SDK-/Bildprojektoptionen bleiben sichtbar. | Keine neue Lizenz an fremden Grafiken/Marken. [NAPS2-Lizenz](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/LICENSE). |
| Apache-/MIT-/BSD-Appbibliotheken | Tatsächlich ausgelieferte Gruppen separat inventarisiert. GPLv3-Auswahl statt GPLv2-only für die App; Originaltexte und Notices aufbewahrt. | Apache-2.0 ist mit GPLv3, nicht GPLv2 kompatibel. [ASF](https://www.apache.org/licenses/GPL-compatibility.html). |
| Freier SANE-Helfer, libusb/JPEG | Bereits aus passenden Quellen gebaut; vollständige Quellen/Patches im bestehenden Kit. `scanimage`/epsonds bleibt eigenständiges GPLv2-Programm; CLI/TIFF-Grenze unverändert. | Kein privater Epson-Treiber und kein geteilter SANE-Adressraum. Die Prozessgrenze ist eine technische Grundlage der getrennten Bewertung, keine universelle Lizenz-Ausnahme. [GNU zu Aggregaten](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation). |
| JPEG-Wrapper | Exakter bereits per Git-Blob mit NuGet-Eingang verbundener Wrappercommit archiviert, dazu jpegli und dessen Highway-/skcms-Pins. CMake baut statisch jpegli/Highway, skcms wird zum Konfigurieren benötigt. | Ein Stammarchiv ohne Git-Submodule war unvollständig. Keine unabhängige Neubaugleichheit dieses fremden Binaries behauptet. [Wrapper](https://github.com/cyanfish/naps2-jpeg/blob/eadca9f4b13cdc75f1c9eec605844063f2782409/CMakeLists.txt). |
| Tesseract | Exakte Wrapper-Submodule für Tesseract, Leptonica, libpng, libjpeg-turbo und zlib archiviert; Apache/BSD/IJG/zlib-Texte erhalten. | Mac-Rezept enthält eigene Hinweise zu Header-/Buildumgebung. Keine neue Behauptung eines vollständigen unabhängigen OCR-Neubaus. [Mac-Rezept](https://github.com/cyanfish/naps2-tesseract/blob/95d99470446d1b87610d20dab8b9ab277b39e5dc/scripts/build-mac-arm64.sh). |
| PDFium | Exakter PDFium-Commit, ursprüngliches Binaries-Buildrezept und 13 gepinnte ausgewählte DEPS-Repositories archiviert, darunter ICU, FreeType, Abseil, JPEG, PNG, zlib und LLVM-Laufzeitteile; FreeType-Alternativtexte ergänzt. | Das Minimal-Mac-Rezept deaktiviert V8/XFA/PartitionAlloc; der gepinnte PDFium-Standard verwendet AGG statt Skia und keine Fontations. Noch keine vollständige ursprüngliche GN-Graph-/Konfigurationsrekonstruktion oder unabhängiger PDFium-Build. [PDFium-DEPS](https://pdfium.googlesource.com/pdfium/+/d3e62278db7489af9e0b686835d1c8aca218c3d7/DEPS), [Originalrezept](https://github.com/bblanchon/pdfium-binaries/blob/a068e5317bb780d0afdf00d8b341938d9f36d2fe/steps/05-configure.sh). |
| Runtime/macOS-Bindings | Assembly-Metadaten belegen .NET-Quellrevision `95017c711e6afc1085133d440e42b4bd78155701` im vereinten `dotnet/dotnet`-Repo und macOS `d813e2baef17cd3a2bb5adc1e37610258d01cda3` in `dotnet/macios`; beide archiviert. | Die Runtime-Revision war im separaten `dotnet/runtime`-Repo nicht vorhanden. Standard-Runtime/Systembibliotheksbewertung nach GPLv3 §1, keine pauschale Microsoft-Ausnahme. Unveränderte allgemeine Buildwerkzeuge sind gesonderte Voraussetzungen. [GPLv3 §1](https://www.gnu.org/licenses/gpl.en.html#section1). |
| OCR-Font | `GlyphlessFont.ttf` bytegleich mit `tessdata/pdf.ttf` des tatsächlich gepinnten Tesseract-Quellstands; Apache-2.0-Nachweis vorhanden. | Kein UI-Font; kein Schluss auf beliebige native interne Fonts. [Fontnachweis](glyphless-font-evidence.json). |

35 zusätzliche Quellarchive sind mit Herkunft, SHA-256 und Nachweisstärke in
[source-supplement.lock.json](source-supplement.lock.json) erfasst. Sie ergänzen
und ersetzen nicht rückwirkend das schon erzeugte Quellenpaket. Das Exportwerkzeug
verlangt für diesen Quellstand `--source-supplement` und erzeugt einen getrennten
Drittquellen-Download. Verfügbare Versionstags und historische Kandidaten werden
nicht zu angeblich bewiesenen NuGet-Quellcommits umbenannt. Bei ZXing enthielt die
Assembly selbst den exakten Commit; dieser unterscheidet sich vom zuerst gefundenen
Versionstag und wurde separat gesichert.

Quellenbeschaffung und unabhängiger Neubau sind verschiedene Nachweise. Eine
unabhängige Reproduktion sämtlicher permissiver Bibliotheken ist nicht pauschal
Voraussetzung jeder Weitergabe. Umgekehrt sind NuGet-Binaries und Lizenztexte allein
kein Ersatz für erforderliche zugehörige Quellen. Der finale Quellenumfang muss
dem ausgelieferten Binärstand entsprechen; identische Binärprüfsummen sind dafür
nicht generell gefordert. [GNU zur Quellen-/Hash-Abgrenzung](https://www.gnu.org/licenses/gpl-faq.en.html#MustSourceBuildToMatchExactHashOfBinary).

## Grafiken: konkret statt pauschal

Der [Grafikbericht](artwork-investigation-2026-10-25.md) führt alle 188 eingebetteten
Dateien mit Hash und Zuordnung auf. 118 sind mit dem offiziellen FatCow-ZIP
bytegleich, elf weitere haben gleiche sichtbare Pixel. 18 vergrößerte Fassungen
sind durch den ursprünglichen NAPS2-Bearbeitungscommit belegt. Das originale
FatCow-README ist aus dem archivierten offiziellen ZIP gesichert und verweist
auf **CC BY 3.0 US**. Attribution, Lizenzlink und Bearbeitungshinweis sind nun
mitgeliefert; kein Copyright an fremden Bildern als eigenes ausgegeben.
[CC-Lizenztext](https://creativecommons.org/licenses/by/3.0/us/legalcode).

Die pauschale frühere Aussage „FatCow-Lizenz unbekannt“ ist damit überholt.
Die Originalwebseite enthält daneben anderslautende Weitergabeformulierungen;
die Original-Archiv-README/CC-Erklärung und dieser Konflikt sind separat
nachvollziehbar. Es wird hier keine gerichtsfeste Auflösung dieses Konflikts
behauptet. Andere Anbieterlogos und nicht zugeordnete Bilder werden nicht unter
FatCows CC-Erklärung subsumiert.

Offen bleiben genau **15 nicht einzeln zugeordnete Bilder**, **16 NAPS2-Branding-
Dateien** und **zehn Anbieterlogo-Dateien**. NAPS2 liefert die Originalgrafiken im
GPL-Projekt; das ist ein reales Lizenzindiz, aber kein separater Marken- oder
Originalautorenbeleg für jede Grafik. Die kleinste Lösung ohne fremde Freigaben
wäre eine eigene neutrale App-/Scanneridentität, generische Mailanbieterbilder
und eigene/Systemsymbole für die übrigen unklaren Raster. Diese Prüfung hat
keine Appgrafik umgestaltet oder entfernt. Anbieter-/Rechteinhaber wurden nicht
kontaktiert. System-AppKit-Symbole werden durch macOS geliefert; keine Apple-
Symbolsammlung wurde neu in die App kopiert.

## Noch nötige Entscheidungen vor einem öffentlichen Release

1. **Grafikstrategie:** Für die oben exakt gelisteten Gruppen entweder den
   spezifischen Grant/Brandingrahmen belegen oder neutrale eigene Ersatzgrafiken
   verwenden. Reiner Rücklink schließt unklare Bildherkunft nicht.
2. **Alte Quellzuordnung:** Für EmbedIO, MimeKitLite, StandardSocketsHttpHandler
   und SWAN sind passende offizielle Versionstags aufbewahrt; für SimpleBase 1.3.1
   ein historischer Kandidat mit passender Versions-/Copyrightangabe. Keine
   deklarierte immutable Paketrevision bei SimpleBase. Für die finale Quellen-
   Freigabe den Ursprung belastbar zuordnen oder einen gezielten Neubau aus dem
   erklärten Quellstand verwenden. Die vorhandenen MIT-/Apache-Grants sind belegt;
   das offene Thema ist Zuordnung, nicht ein behauptetes neues Nutzungsverbot.
3. **PDFium-Abschluss:** Den tatsächlichen minimalen Build-/Subquellgraph mit dem
   Binärstand abgleichen; Archive/Notices sind jetzt vorhanden. Kein neuer
   Hardwaretest kann diese Quellenfrage ersetzen.
4. Developer ID/Notarisierung und spätere reguläre Erststartprüfung bleiben
   unabhängig von dieser Quellen-/Grafikprüfung. Die bestehende LGPL-Ersatz-
   prüfung ist technische Verifikation und hier nicht als allgemeine neue
   Copyright-Erlaubnis erfunden.

## Lokale Implementierung und Nachweise

- Unnötige alte SANE-Paketreferenz entfernt und durch Abwesenheitsprüfung gesichert:
  das alte lokale Bundle fällt durch die gezielte Kontrolle; der neue Kontrollbuild
  besteht sie. Kein SANE-Lizenztext wurde entfernt, um Code scheinbar umzudeklarieren.
- About-Dialog des markierten ES60W-Builds bietet `Lizenzen & Quellen` auf den
  lokalen HTML-Index. Nur vollständiger App-/Registrar-Neubau, keine DLL-Ersetzung.
- 112 Lizenzdateien in Quellbaum und Kontroll-App hashgleich; 35 ergänzende
  Quellarchive nach SHA-256 geprüft; 24 native Dateien nur mit gebündelten oder
  Systemabhängigkeiten. Frischer HOME-/Worker-Start und künstlicher PDF-Pfad
  bestanden. Der lokale Lizenzlink ist kompiliert und sein Ziel vorhanden;
  ein tatsächlicher Klick im Dialog wurde nicht als geprüft ausgegeben.
- Die akzeptierte App, AutoSize-App, aktive Entwicklungskopie und ursprüngliche
  Release-DMG/App bleiben unverändert. Kein neuer echter Scan/Gerätebefehl,
  kein Paperless-Upload, kein Git-Push und keine Veröffentlichung.

[Strukturierte Nachweise](rights-evidence-2026-10-25.json),
[statischer Prüfcode](check-release-rights-inputs.py).
