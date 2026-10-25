# Begrenzter Grafikrechte-Nachweis – NAPS2 ES60W, 2026-10-25

**Ergebnis:** FatCows Lizenz lässt sich aus archivierten **Originalquellen** belegen: CC BY 3.0 **US**, nicht bloß eine unbestimmte CC-Lizenz aus einem Mirror. Das schließt die bisherige Quellenlücke, aber keine pauschale Grafikfreigabe: Die Originalwebseite enthält widersprüchliche Weitergabeformulierungen; App-Branding, abgeleitete Bilder und Anbieterlogos benötigen eine getrennte Bewertung. Ein tatsächlich eingebetteter OCR-Font ist nachweisbar Tesseracts `pdf.ttf` (Apache-2.0).

## Gegenstand und Nachweismethode

- Fork: `<local ES60W release checkout>`; Branch `es60w-macos-release`, HEAD `efa99563f478d4776282421d76616e73a938d2f2`; Basis 8.5.1, `3481963789af647a9f9e0a19176a0d2f7f593b5d`.
- Bundle: `<local 8.5.1-es60w.1 app bundle>`. Pfade mit `Contents/` beziehen sich darauf; andere Assetpfade auf den Fork.
- Ausschließlich statisch: Quellaufrufe, Ressourcenreferenzen, Dateiinventar, SHA-256 und Vorkommen vollständiger Assetbytes in den ausgelieferten Assemblies. Keine Laufzeitbeobachtung: „benutzt“ bedeutet hier vom macOS-Code ausgewählt/erreichbar; bedingte und nur mitgelieferte Ressourcen werden getrennt benannt. Externe ZIPs wurden nur im Speicher gelesen.
- `NAPS2.Lib/Icons.resx` referenziert **193 Schlüssel auf 188 unterschiedliche Dateien**. Alle 188 Dateiinhalte kommen vollständig und bytegleich in `Contents/MonoBundle/NAPS2.Lib.dll` vor. Eine Ressourcendatei kann über mehrere Schlüssel angesprochen werden. Diese Bilddateien und `NAPS2.App.Mac/Icon.icns` sind gegenüber der genannten Upstream-Basis unverändert. Der Git-Klon ist shallow; fehlende lokale Historie wurde nur für einzelne relevante Dateien über das offizielle NAPS2-Repository ergänzt.

| Prüfanker | SHA-256 |
|---|---|
| `Contents/Resources/Icon.icns` = `NAPS2.App.Mac/Icon.icns` (88.832 Bytes) | `8e91a026551d059a16c59c9c0190d0480168755d8f06ae4bac1315cf87f09e12` |
| `Contents/MonoBundle/NAPS2.Lib.dll` | `5d989920765dedfbbafa4fe1b6dea55563d0312b7b6a65993cd871ed28ef972a` |
| `Contents/MonoBundle/NAPS2.Lib.Mac.dll` | `954b2957f0ede72a948e4f432b7ee3dd5d553306140552329a14709dacb22d16` |
| `Contents/MonoBundle/NAPS2.Sdk.dll` | `2aecd47e0fa3f5410850a908bee783fca94930e5069d98dc9cebe758f62356dc` |
| `NAPS2.Lib/Icons.resx` | `011a47f56fb2dc6daa800b554d39cf7ea9a9edcabf4e82195b4c7a65227ad2ae` |
| `NAPS2.Sdk/Pdf/GlyphlessFont.ttf` (572 Bytes) | `c7845420925a23d88ed830a63957b8af85a66a8daf8d9fc90e843673b2ef1a59` |

## Tatsächliche Auswahl im macOS-Bundle

| Gruppe | Verwendung und konkrete Pfade | Rechtebeleg / Grenze |
|---|---|---|
| App-Icon / NAPS2-Scannerbranding | `Info.plist`: `CFBundleIconFile=Icon.icns`. `Icons/scanner-128.png` wird direkt in `AboutForm` und für das Freigabe-Geräteicon verwendet; `favicon.ico` wird in Desktop-/Vorschaufenstern geladen. Profilbilder wählen `scanner-48-rev2.png`, `scanner-default-rev2.png`, `scanner-lock-rev2.png`, `scanner-lock-default-rev2.png`, `scanner-wireless-rev2.png`; bei dem macOS-Skalierungsfaktor 2 deren `scanner-96.png` bzw. `scanner-*-hires.png`. Tray-Funktion: `scanner-32-gray.png`. Alle Bildpfade hier unter `NAPS2.Lib/Icons/`. | Die Dateien werden vom offiziellen NAPS2-Projekt unter dessen GPL-Projektrahmen ausgeliefert. Das ist ein belegter Zuordnungsansatz, **kein individueller Urheber-/Markenrechtsnachweis** für jedes Bild. Kein spezifischer Grafikgrant/Branding-Policy in den untersuchten Stellen gefunden. Der [Mac-Icon-Commit](https://github.com/cyanfish/naps2/commit/dbe9714ebd48131468af31404e266fa4b4a99e8b) dokumentiert eine Auflösungsänderung, keine eigenständige Rechteerklärung. |
| macOS-Systemsymbole | `MacIconProvider` ordnet 51 Namen System-Symbolen zu, etwa Scan → `play`, Profile → `list.bullet`, PDF → `doc.richtext`, Drehen → `arrow.counterclockwise`, Löschen → `trash`. `_small` wird ggf. entfernt. `NSImage.GetSystemSymbol` liefert die Bilder; bei fehlendem Symbol greift der eingebettete Fallback. | Systembereitstellung durch AppKit, keine separat mitgelieferten SF-Symbol-Bilddateien festgestellt. Daraus folgt keine freie Lizenz an Apple-Symbolen. [Apple API](https://developer.apple.com/documentation/appkit/nsimage/init(systemsymbolname:accessibilitydescription:)), [NAPS2 MacIconProvider](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/NAPS2.Lib.Mac/EtoForms/Mac/MacIconProvider.cs). |
| Eingebettete UI-Bilder / FatCow | macOS benutzt weiterhin Rasterbilder, z. B. `cog.png`, `copy.png`, `paste.png`, `undo.png`, `redo.png`, `keyboard.png`, `zoom_in.png`, `zoom_out.png`, sowie `broom-hires.png`, `email_attach-hires.png`, `picture_edit-hires.png`, `printer-hires.png`, `text-hires.png`, `world-hires.png`, `network_ip-hires.png`, `device-hires.png`. Konkrete Auswahl hängt von Dialog, Befehl und Skalierung ab. | 118 der 188 Dateien bytegleich mit dem offiziellen FatCow-Standardarchiv; weitere 11 haben identische sichtbare RGBA-Raster nach Normalisierung unsichtbarer RGB-Werte. Der Anhang unterscheidet diese Nachweisstärken. Nicht alle übrigen Dateien dürfen deshalb FatCow oder GPL zugeordnet werden. |
| Mailanbieterbilder | `apple_mail.png` / `apple_mail-hires.png` sind im Apple-Mail-Auswahleintrag erreichbar, auch wenn dieser deaktiviert ist. `gmail*`, `outlookweb*`, `outlooknew*`, `thunderbird*` werden mitgeliefert. Thunderbird wird nur unter Linux ergänzt; neues Outlook verlangt Windows. Gmail/Outlook Web hängen von Client-Credentials ab; dieses Bundle enthält `NAPS2.ClientCreds-.resources` (Platzhaltervariante). | [EmailProviderController](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/NAPS2.Lib/ImportExport/Email/EmailProviderController.cs) und lokaler `NAPS2.Lib.Mac/ImportExport/AppleMailEmailProvider.cs`. Der offizielle [Icon-Update-Commit](https://github.com/cyanfish/naps2/commit/74f604cd27e80b042b4ad6578d700dc6c66dfc6d) belegt Einbringung/Änderung, aber keine Nutzungserlaubnis der Anbieter. **Keine spezifische Freigabe festgestellt; keine FatCow-Pauschalzuordnung.** |
| Nicht verwendete Quelldateien | 13 Dateien in `NAPS2.Lib/Icons/` sind nicht in `Icons.resx`: alte `scanner-*-rev1.png` / `scanner-16-rev0.png`, `help.png`, `wireless16_filled.png`, `wireless_filled.png`, `btn_donate_LG.gif` (vollständige Ausschlussliste unten). | Nicht zum aktuellen UI-Ressourcensatz zählen. Die vollständigen Bytes von Spenden-GIF, `help.png`, `wireless_filled.png` und altem Scanner-Icon wurden zusätzlich im Bundle-DLL gesucht und nicht gefunden. Der aktuelle Spendenknopf wird als Textknopf erzeugt. |

Die macOS-Entscheidung ergibt sich aus `NAPS2.Lib.Mac/EtoForms/Mac/{MacEtoPlatform,MacIconProvider}.cs` (`GetScaleFactor => 2f`, Form-Icons über Provider sind `null`), `NAPS2.Lib/EtoForms/DefaultIconProvider.cs`, `EtoForms/Ui/{DesktopCommands,AboutForm,ServerTrayIndicator}.cs` und `EtoForms/Widgets/{ProfileListViewBehavior,SharedDevicesListViewBehavior}.cs`. [Upstream-Ressourcenzuordnung](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/NAPS2.Lib/Icons.resx), [DefaultIconProvider](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/NAPS2.Lib/EtoForms/DefaultIconProvider.cs).

## FatCow: ursprünglicher Lizenztext und offizielle Archivkette

1. **Originalseite, archiviert am 2016-03-01 12:06:38 UTC:** [FatCow free-icons](https://web.archive.org/web/20160301120638/http://www.fatcow.com/free-icons), [abgerufene Original-HTML-Fassung](https://web.archive.org/web/20160301120638id_/http://www.fatcow.com/free-icons). HTML: 16.342 Bytes, SHA-256 `100509ba3cd993720bf6d133b372a79560067d537e89c4b25d9171ab1458aede`. Original heute beim Abruf zur Network-Solutions/iPage-Seite umgeleitet bzw. mit HTTP 403 beantwortet.
2. Dort steht: **“These icon sets are licensed under a Creative Commons Attribution 3.0 License.”** Der Lizenzbutton verlinkt tatsächlich auf `http://creativecommons.org/licenses/by/3.0/us/`. Die Seite erlaubt private/kommerzielle Softwareverwendung und verlangt in den Credits einen Rücklink auf `http://www.fatcow.com/free-icons`. Zugleich untersagt sie Verkauf, Unterlizenzierung, Vermietung, Übertragung und weiteres Bereitstellen. Im `title` des Lizenzbuttons kommt die zusätzliche Wendung **“including uploading the font archive to publicly available websites”** vor. Diese Inkonsistenz wird nicht zu einer eindeutigen zusätzlichen oder aufgehobenen Lizenzbedingung umgedeutet. [Archiviertes Original](https://web.archive.org/web/20160301120638id_/http://www.fatcow.com/free-icons), [CC BY 3.0 US Legal Code](https://creativecommons.org/licenses/by/3.0/us/legalcode).
3. **Offizielles ZIP**, von derselben Seite verlinkt: [Original-URL](http://www.fatcow.com/images/fatcow-icons/fatcow-hosting-icons-3.9.2-all.zip), [archiviertes Original vom 2014-07-02 16:36:59 UTC](https://web.archive.org/web/20140702163659id_/http://www.fatcow.com/images/fatcow-icons/fatcow-hosting-icons-3.9.2-all.zip). Tatsächlich gelesener ZIP-Body: **32.652.636 Bytes**, SHA-256 `7422e7aa7b3bc6ce21a937287a27501c5a5307dfc978a34e978d8d9948f80a9e`. Das ist die heruntergeladene Dateigröße; CDX-Speicherlängen sind kein Ersatz dafür.
4. Darin liegt `fatcow-hosting-icons-3.9.2.zip`: 11.790.312 Bytes, SHA-256 `786cf58bda7176fd3fe1faf4956c9003afb9822c8392099afa29d0b8ea05d7e0`. Dessen `readme-fatcow.txt` (SHA-256 `c81c10c29ef9f7ddbf39bfae9d77f7d6e76dd37ded12938d68808ca8257beca6`) nennt ausdrücklich CC Attribution 3.0 mit US-Lizenzlink, FatCow Web Hosting, Copyright 2009–2014, und fremde Marken-/Urheberrechte. Die zusätzlichen Weitergabeverbote der Webseite stehen dort nicht. **Das README wurde aus dem offiziellen archivierten ZIP gelesen, nicht aus einem GitHub-Mirror übernommen.**

Upstream dokumentiert die Vergrößerung vieler `*-hires.png` mit waifu2x im [Commit 3ed00b9](https://github.com/cyanfish/naps2/commit/3ed00b932c0f8b5be653af78e26495f9eff18e5e). Das belegt Bearbeitung, nicht neue Rechte an der Vorlage. Bei einer Attribution sind vergrößerte/bearbeitete Fassungen als solche kenntlich zu machen. `AboutForm` enthält schon „Icons from:“ samt FatCow-Link, aber keinen CC-US-Lizenzlink und keinen Bearbeitungshinweis; in den untersuchten separaten Bundle-Textnotizen fand sich kein FatCow-Nachweis. [AboutForm](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/NAPS2.Lib/EtoForms/Ui/AboutForm.cs).

## Fonts und NAPS2-GPL-Zuordnung

- Keine eigenständigen `.ttf/.otf/.ttc/.woff`-Dateien im Bundle gefunden. UI-Code nutzt vorhandene Eto-/macOS-Systemfonts, etwa `NSFont.BoldSystemFontOfSize(12)`; der Spendenknopf verändert die bestehende Fontfamilie.
- **Tatsächlich eingebettet:** `NAPS2.Sdk/Pdf/GlyphlessFont.ttf`, Ressource `NAPS2.Pdf.GlyphlessFont.ttf` in `Contents/MonoBundle/NAPS2.Sdk.dll` (vollständiger Byteinhalt ab Offset 207626). Wird durch `GlyphlessFont.LoadFontProgram()` geladen und in `PdfExporter` für unsichtbaren OCR-Text in exportierte PDFs eingebettet; kein UI-Font. Bytegleich mit [Tesseract 5.5.1 `tessdata/pdf.ttf`](https://raw.githubusercontent.com/tesseract-ocr/tesseract/5.5.1/tessdata/pdf.ttf). [Tesseracts LICENSE](https://github.com/tesseract-ocr/tesseract/blob/5.5.1/LICENSE) ist Apache-2.0; [dessen Buildzuordnung](https://github.com/tesseract-ocr/tesseract/blob/5.5.1/tessdata/Makefile.am) führt `pdf.ttf` als auszuliefernde Datei. Lokale Aufruf-/Einbettungsbelege: `NAPS2.Sdk/NAPS2.Sdk.csproj:91`, `NAPS2.Sdk/Pdf/GlyphlessFont.cs:163`, `NAPS2.Sdk/Pdf/PdfExporter.cs:69` und `:172`.
- Weitere applikationseigene Fontressourcen nicht festgestellt; die Suche nach Fontdateinamen in den Bundle-Assemblies ergab nur obige TTF-Ressource (neben Fontformat-Klassennamen). Das ist keine erschöpfende Untersuchung komprimierter/native-intern eingebetteter Bibliotheksfonts. Diese verbleiben ausdrücklich in der Bibliotheksprüfung des Hauptagenten.
- [NAPS2 LICENSE](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/LICENSE) und [README](https://github.com/cyanfish/naps2/blob/3481963789af647a9f9e0a19176a0d2f7f593b5d/README.md#license) ordnen das Programm GPL-2.0-or-later zu, mit separaten Optionen einzelner Projekte. Das ersetzt keine abweichenden FatCow-, Font- oder Anbieterrechte und begründet keine allgemeine Markenfreigabe.

## Genau offene Punkte und kleinste praktische Lösung

1. **FatCow-Nachweis sichern und Attribution konkretisieren:** Autor/Set, Originalseite, Archivlink, **CC BY 3.0 US** samt Lizenz-URL und Hinweis auf Bearbeitung/Vergrößerung in einer mitgelieferten Artwork-Notiz zusammenführen; About-Link erhalten. Vorschlag für eindeutig zugeordnete FatCow-Assets: `Farm-Fresh Web Icons © 2009–2014 FatCow Web Hosting, CC BY 3.0 US; Quelle: http://www.fatcow.com/free-icons; einzelne Fassungen durch NAPS2 verändert/vergrößert.` Das schließt die Dokumentationslücke, aber entscheidet den Konflikt Webseite/README/CC-Rechtstext nicht. Keine Behauptung, ein Rücklink allein beseitige alle Weitergabefragen. [CC-Pflichten §§ 3–4](https://creativecommons.org/licenses/by/3.0/us/legalcode).
2. **NAPS2-Branding und nicht exakt zugeordnete Ableitungen:** Spezifischer Urheber-/Lizenznachweis fehlt für die Scanner-/App-Icon-Familie und die im Anhang mit `O` markierten Dateien; bei `H` ist nur die Upstream-Bearbeitung belegt. Kleinster Weg ohne neue Rechteanfrage und ohne verbleibende Grafik-Herkunftslücke: eigene schlichte App-/Scannerbilder einsetzen und unbekannte UI-Bilder durch bereits verwendete AppKit-Systemsymbole oder eigene einfache Zeichnungen ersetzen. Dabei auch nicht mehr benötigte `Icons.resx`-Einträge entfernen; bloßes Nichtanzeigen entfernt die mitgelieferten Dateien nicht. Die bestehende GPL-Zuordnung als Indiz kann dokumentiert werden, nicht als erfundener individueller Grant.
3. **Mailanbieterlogos:** Für den tatsächlich erreichbaren Apple-Mail-Knopf generisches Mail-Symbol oder Text verwenden; die anderen acht nur mitgelieferten Gmail-/Outlook-/Thunderbird-Dateien aus Ressourcen entfernen, falls der macOS-Fork sie nicht braucht. Im Rahmen dieser Prüfung keine separate Bildlizenz gefunden. Der NAPS2-Commit und Anbietername reichen dafür nicht.
4. **Glyphless-Font:** TTF mit obigem Hash dem Apache-2.0-Nachweis ausdrücklich zuordnen und vollständigen Lizenztext mitliefern. `Contents/Resources/LicenseReview/packages/NAPS2.Tesseract.Binaries-1.4.0/` enthält in diesem Bundle nur `tesseract-authors.txt`; eine fontbezogene Zuordnung fehlt. Abgleich/Integration in den ohnehin parallel bearbeiteten Bibliotheksnachweisen genügt; kein neuer Font nötig. [Apache-2.0 § 4](https://www.apache.org/licenses/LICENSE-2.0).

Dies sind Folgeoptionen; **hier wurde ausschließlich diese Berichtsdatei angelegt**. Keine Assets ersetzt, kein Build/Appstart/Scan, keine Bibliotheksquellen erneut auditiert, kein Commit/Push, keine Veröffentlichung und keine Rechteinhaber kontaktiert. Der Nachweis ist technisch und quellenbezogen begrenzt; er ist keine juristische Komplettfreigabe.

## Prüfanhang: vollständige Assetpfade und SHA-256

`F`: bytegleich mit einer PNG im offiziellen FatCow-Standard-ZIP. `R`: sichtbares Raster identisch (PNG-Dekodierung; RGB bei Alpha 0 normalisiert), Dateibytes verschieden. `H`: im genannten Upstream-Upscaling-Commit enthalten; diese Herkunftsmarkierung allein ist kein Lizenzgrant. `B`: Scanner-/App-Branding mit offener spezifischer Zuordnung. `M`: Mailanbieterbild, separate Rechte offen. `O`: sonstige Datei ohne hier geschlossenen Herkunftsnachweis. Alle folgenden Dateien sind **mitgeliefert**; daraus folgt nicht, dass jeder Dialog sie auf macOS anzeigt. Für `F`/`R` steht zusätzlich der konkrete Pfad innerhalb von `fatcow-hosting-icons-3.9.2.zip`.

<details>
<summary>188 eingebettete Quelldateien, vollständige Hashliste und FatCow-Zuordnung</summary>

```text
9a2683eafac245dfa848cbc6267542f141b098aca7343cd977a266b095b6741c  NAPS2.Lib/Icons/accept-small.png  [F]  <- FatCow_Icons16x16/accept_button.png
88e3ac53e6b15dbbbb8bb9a8766d5c795e6294d0cf67ccbea961877581655faa  NAPS2.Lib/Icons/accept.png  [F]  <- FatCow_Icons32x32/accept_button.png
da87e981344895c580f2be444fb506da0cb20df4b5bd4f9d4880d7bfac7caf19  NAPS2.Lib/Icons/add-small.png  [F]  <- FatCow_Icons16x16/add.png
3ba6618db957c1b2e64392897324ca48880d63cc2985fe7ec14750439a96f575  NAPS2.Lib/Icons/add.png  [F]  <- FatCow_Icons32x32/add.png
f587437249345be131f90049bb97c0d0a1bac681ef91077cd844572ebe6fd7bd  NAPS2.Lib/Icons/apple_mail-hires.png  [M]
1f48f76e879afd2a93e0307e95e5fb2677a149e07643a088a731a26448a6fae4  NAPS2.Lib/Icons/apple_mail.png  [M]
7e066fc66d1259389d01a127471eb75a5eb98c270507723228859eaef374589d  NAPS2.Lib/Icons/application_cascade-small.png  [F]  <- FatCow_Icons16x16/application_cascade.png
088639852ad0d6ed9ed17796b6524c57756ca2fa7ad920aa155fe85530a19530  NAPS2.Lib/Icons/application_cascade.png  [F]  <- FatCow_Icons32x32/application_cascade.png
b2c9649d10d19b661f403a335672330daba40e5bd6f75c6500ff3e462e089e6e  NAPS2.Lib/Icons/application_side_list-small.png  [F]  <- FatCow_Icons16x16/application_side_list.png
b7418635c909940033d70b68a7a50885c191748b6028220544da6289efc173c4  NAPS2.Lib/Icons/application_side_list.png  [F]  <- FatCow_Icons32x32/application_side_list.png
7a5b04256294ead2e42ccf8f98aecd39b530c1af69ac586eb72f73578cd7a88a  NAPS2.Lib/Icons/arrow_down-small.png  [F]  <- FatCow_Icons16x16/arrow_down.png
bca4eb158c9d630e714bf72cc920f4b572d5e23b920a85f26f5e7119caf81714  NAPS2.Lib/Icons/arrow_down.png  [F]  <- FatCow_Icons32x32/arrow_down.png
ebae26728bf4054c4cd2bc8b2d6c364076d3b0dcdbaba49ad3b6d3fbc4ab9b0d  NAPS2.Lib/Icons/arrow_left-small.png  [F]  <- FatCow_Icons16x16/arrow_left.png
ced6b2267fddce021063eb774e78387c6872ba990bb41516ec6e63ef1124c831  NAPS2.Lib/Icons/arrow_left.png  [F]  <- FatCow_Icons32x32/arrow_left.png
465a98f6b5d6564bc54cc82d2f43fc54e25639d461a418660614f5bae935a4aa  NAPS2.Lib/Icons/arrow_out-small.png  [R]  <- FatCow_Icons16x16/arrow_out.png
0fcb12c3218fa8d818f24a2b230d847adf02bb6f5b286d5bb60ba76dadf39750  NAPS2.Lib/Icons/arrow_out.png  [F]  <- FatCow_Icons32x32/arrow_out.png
1b52289bf0eb3c60bb2810e1426320ab3a5c3939947d57b50bb4d11421fbd565  NAPS2.Lib/Icons/arrow_refresh-hires.png  [H]
d0460e44ff1b6e4823cb6593ec540df9345febd446492baec4c0189b00d6a625  NAPS2.Lib/Icons/arrow_refresh.png  [F]  <- FatCow_Icons32x32/arrow_refresh.png
ff8d3907ca7259adca51cb47b2da3131b94d6c6fcab161064222010adf6e836e  NAPS2.Lib/Icons/arrow_right-small.png  [F]  <- FatCow_Icons16x16/arrow_right.png
9629c2513a1d3d99841daec3f68eb51b9105d03a23a01e09420b1c1d24f10bbf  NAPS2.Lib/Icons/arrow_right.png  [F]  <- FatCow_Icons32x32/arrow_right.png
ce5b93622ceaa7d4f81f0c47d1f3769d9719a3da71da22f488c865817efde932  NAPS2.Lib/Icons/arrow_rotate_anticlockwise-hires.png  [H]
9fc2fda7106b1778b3b0706cdbbf4530defb2108a431ee470d95b9556d7509ee  NAPS2.Lib/Icons/arrow_rotate_anticlockwise-small.png  [F]  <- FatCow_Icons16x16/arrow_rotate_anticlockwise.png
1080c268f5c32564b8b2484e8ec36637505dcae8427b85fe642a2e09ea573515  NAPS2.Lib/Icons/arrow_rotate_anticlockwise.png  [R]  <- FatCow_Icons32x32/arrow_rotate_anticlockwise.png
47685ce2c57aa05792af3c11f37eedab96d719d5dd1f9ffd1dd57ee3824f0ec4  NAPS2.Lib/Icons/arrow_rotate_clockwise-small.png  [F]  <- FatCow_Icons16x16/arrow_rotate_clockwise.png
bdd8aff71a4a939e75f8df094f8e26d3141a8fb8c8a99be1a66ddb7227345fd9  NAPS2.Lib/Icons/arrow_rotate_clockwise.png  [R]  <- FatCow_Icons32x32/arrow_rotate_clockwise.png
e2bc06d82f25011a44fa7a843dc383da3257bfc5d3a30c5cab28093e387c92ce  NAPS2.Lib/Icons/arrow_switch-small.png  [F]  <- FatCow_Icons16x16/arrow_switch.png
27ab4b7b05cb1b43cac2c3358e217bd0ac9424b30149840dad8b8ac8231295d5  NAPS2.Lib/Icons/arrow_switch.png  [F]  <- FatCow_Icons32x32/arrow_switch.png
40568abfb4dd17342fc587be4a846ea745ad74d4890f3fef505414e7b51903d7  NAPS2.Lib/Icons/arrow_up-small.png  [F]  <- FatCow_Icons16x16/arrow_up.png
a254b73f2cda68d943892bb1fb8edff12a355e1771408849c61b182751fa97ff  NAPS2.Lib/Icons/arrow_up.png  [F]  <- FatCow_Icons32x32/arrow_up.png
4172a9ace1547fa9c49418f8ab137bbdf09d6cbf0702fd13ca1abd032f812890  NAPS2.Lib/Icons/ask-hires.png  [H]
dadc9c4470e4cd5ee157bd499e0726beae41e2fb4408b791972943a991c0959a  NAPS2.Lib/Icons/ask.png  [O]
c73bf1ea65b424b7956ab9ec48da6560edf4805273ad61f0f4e75c7c2aad62fb  NAPS2.Lib/Icons/blueprints-hires.png  [H]
af82ef5787f8aff1aac848df0a12b05b09219a898e9ce6f35aae6d228327508b  NAPS2.Lib/Icons/blueprints-small.png  [F]  <- FatCow_Icons16x16/blueprints.png
472c466e94bcd2fef874717ed28addd3d3c69f623e1a6ff1c530ffbacce3b4d9  NAPS2.Lib/Icons/blueprints.png  [F]  <- FatCow_Icons32x32/blueprints.png
fbff0c7547814fa9ab4e48acf74651f1dc1bfc729cb263a05b71089aec9e2f08  NAPS2.Lib/Icons/broom-hires.png  [H]
abe813c9b1129d495e9ad2de555a114c802bf42b45dd5b62f84920c4a5ee144d  NAPS2.Lib/Icons/broom.png  [F]  <- FatCow_Icons32x32/broom.png
77e4bf1b71f2742cc645c4cd3998d6f1c6fca7e478e42715f108eff0eb180dd1  NAPS2.Lib/Icons/cancel-hires.png  [H]
03e31685554582ec7331a4f364c72d159da6271742bd23027b26adff05b9fb5e  NAPS2.Lib/Icons/cancel-small.png  [F]  <- FatCow_Icons16x16/cancel.png
3feec157c74b46ae11dbc106bf7215beea88f73f28644ea831804f2d4fffd2b1  NAPS2.Lib/Icons/cancel.png  [F]  <- FatCow_Icons32x32/cancel.png
93d32d076d4f6e4d2570a95bc504592de2cfa1b7244cfd447423f9a2ff380762  NAPS2.Lib/Icons/close.png  [O]
9b15c687dc9e4aebe320b6c8a8e44616657b3134ce2c29ffab0647322ef4d906  NAPS2.Lib/Icons/cog-small.png  [F]  <- FatCow_Icons16x16/cog.png
c405f27fb7f1a5cecb8fa1a776417f2d690d05a1793b054711f13d25c3807aef  NAPS2.Lib/Icons/cog.png  [F]  <- FatCow_Icons32x32/cog.png
e8394874a9260f22f75ca2fe03f7138e73f24c91f10f12cfe9f627ce11d9bbef  NAPS2.Lib/Icons/color_gradient-small.png  [F]  <- FatCow_Icons16x16/color_gradient.png
eef8f6c99465567721c8c9c705c34858d8444ffe1674997b936a55c284af180b  NAPS2.Lib/Icons/color_gradient.png  [F]  <- FatCow_Icons32x32/color_gradient.png
5202065a6482a9788a182c099f250a168a6c1e273c85d80987eac40cd7176dc7  NAPS2.Lib/Icons/color_management-small.png  [F]  <- FatCow_Icons16x16/color_management.png
0e5b374e04effc9be96c831163c15ae4e0011fd2537e5114850b63a978b37d30  NAPS2.Lib/Icons/color_management.png  [F]  <- FatCow_Icons32x32/color_management.png
80ba9f887425c61c227babdef984dec3dcd5a9e4bbbe23d752d7de404b9b0dc0  NAPS2.Lib/Icons/color_wheel-small.png  [F]  <- FatCow_Icons16x16/color_wheel.png
b5d4ea910ad7404a795cd631a52a00003e82d7d572b3fc529e71efdad7442b2e  NAPS2.Lib/Icons/color_wheel.png  [F]  <- FatCow_Icons32x32/color_wheel.png
43b50ae7d26873e295f8ba35c05df75c4d8e185dbbcd7bb5498194e3ae25a1c0  NAPS2.Lib/Icons/column_double-small.png  [F]  <- FatCow_Icons16x16/column_double.png
aea9d65f70541f8156af69de73a4d90ef056ca326c154c7acb609171822c9205  NAPS2.Lib/Icons/column_double.png  [F]  <- FatCow_Icons32x32/column_double.png
dd89ce4cf45c88a63ae36b5c78870b159e7d28db099e0dca69c562e4b6ca573b  NAPS2.Lib/Icons/combine-small.png  [F]  <- FatCow_Icons16x16/split_panel_vertical.png
c412075436605f0110c6e507033d439149c13542b0e279b19e20011bfa17204e  NAPS2.Lib/Icons/combine.png  [O]
c2ac6a3ce75f74f26e055b95cf002aebd0ffb658386b25adf6bb0f82c4f99cd4  NAPS2.Lib/Icons/combine_hor-small.png  [F]  <- FatCow_Icons16x16/split_panel.png
eca9534faaa5a52b75b4d2d5aac9a492bb5b0c5309315446fe70814a57e60155  NAPS2.Lib/Icons/combine_hor.png  [O]
c8db7c4d944f8567edbf4debaa4338d08352cf5e62f70b308a1ba423c1711a8d  NAPS2.Lib/Icons/contrast-small.png  [F]  <- FatCow_Icons16x16/contrast.png
c0c3c2372c0a7915dca943dd58ead680ac02d4b4d0d6ae6fa1c29ff8738963ab  NAPS2.Lib/Icons/contrast.png  [R]  <- FatCow_Icons32x32/contrast.png
e627632c808b8529b433a415b223f2a884d650b722e333ca98f2b05808d0552d  NAPS2.Lib/Icons/contrast_high-small.png  [F]  <- FatCow_Icons16x16/contrast_high.png
52157d28d0fb322269191834c09688f8e13ad5425a085dd04eae85d84b4f479c  NAPS2.Lib/Icons/contrast_high.png  [F]  <- FatCow_Icons32x32/contrast_high.png
adc112a5ca40528eee6070f8cc97f97ac4127500c516b2e86231c425cd285e9e  NAPS2.Lib/Icons/contrast_with_sun-small.png  [O]
655911e4f76e392ebe29cc8f2f41b2a931efd00aa64ba9e055ac0cd3293ab7c1  NAPS2.Lib/Icons/contrast_with_sun.png  [O]
f96abf33d7edf4c4da208f74dd65154c13230ea8d249e88e6a604975eafd204d  NAPS2.Lib/Icons/control_play_blue-hires.png  [H]
d5d7e4d050baa84c616643f7a9a3068014f3a3b724ebddc19e9bbb9646fe9dc3  NAPS2.Lib/Icons/control_play_blue-small.png  [F]  <- FatCow_Icons16x16/control_play_blue.png
700c1539e7f4713807dc1428bafa0b86fa5f753b331e174e306d04ba5114362b  NAPS2.Lib/Icons/control_play_blue.png  [F]  <- FatCow_Icons32x32/control_play_blue.png
eaad37f80a88e470364973a2236e9fe4f6d19079b739ec731f7a02d26556a8c9  NAPS2.Lib/Icons/copy-small.png  [F]  <- FatCow_Icons16x16/page_copy.png
c06c37d7e9a1ed43f7538eea6b86ef94c7186466f6d7988a98c70189a0a17031  NAPS2.Lib/Icons/copy.png  [F]  <- FatCow_Icons32x32/page_copy.png
5756d0f760d562858a2a551418539a5e0f88e45c3c3d6fe3b63eaa8c5f90455b  NAPS2.Lib/Icons/cross-hires.png  [H]
90e43f3101637c878b993641d87610047390c8ce5f6630484cf56f5e45083fbf  NAPS2.Lib/Icons/cross-small.png  [F]  <- FatCow_Icons16x16/cross.png
14912c25992125463cd7d82e7d89ed7c514969f56d3f51c7714d14646fb17669  NAPS2.Lib/Icons/cross.png  [R]  <- FatCow_Icons32x32/cross.png
e0244becf4d1b02970675f81d27289b2696b1c7be4f4615d1f3c64c0b5c1ce5d  NAPS2.Lib/Icons/device-hires.png  [H]
0eb59e83e776ee4c4d0c7ae4d540b3639ac7cc67dc8f3ac91c50c49d3d91418f  NAPS2.Lib/Icons/device.png  [F]  <- FatCow_Icons32x32/scanner.png
456e8509b2389ddaec8875bf35f6698c1315a53768b47c579577b450ed484baa  NAPS2.Lib/Icons/document-small.png  [F]  <- FatCow_Icons16x16/text_dropcaps.png
17cac3cf58fc6338b5050ad26c6f2478c9ee1a8bcd6568832a8131ae68c9cdf7  NAPS2.Lib/Icons/document.png  [F]  <- FatCow_Icons32x32/text_dropcaps.png
3e597726ddd1467fc14b43e66841a2d354a62e05bb1f02c8a2566de5878b6874  NAPS2.Lib/Icons/draw_ellipse-small.png  [F]  <- FatCow_Icons16x16/draw_ellipse.png
fc7ca64bf217c4065dbad3724fa6c1f7b2494aad897a10563571e937d9d0e66c  NAPS2.Lib/Icons/draw_ellipse.png  [F]  <- FatCow_Icons32x32/draw_ellipse.png
b94316b53c9787945527f11bae8d510ed4dd921506c7c6c58110d2d1899fbd86  NAPS2.Lib/Icons/email-small.png  [F]  <- FatCow_Icons16x16/email.png
b7b451ac6371a1101aee9feb5044c167bdf0878f9f3029d816ba7cfc2e26b6f8  NAPS2.Lib/Icons/email.png  [F]  <- FatCow_Icons32x32/email.png
6944b88a094f8e121070bd90cbe9982087bca34f02dcb530afd9c1d0f5ae6b5c  NAPS2.Lib/Icons/email_attach-hires.png  [H]
9f655e7e04e4fd166da033611aa9498c8079e04702784e1d0ba33193a5002a8b  NAPS2.Lib/Icons/email_attach.png  [R]  <- FatCow_Icons32x32/email_attach.png
80611daa4882c8c3033c86a66ab9227eaf28e6d8cc0dfc8023bbe28f5b49f8e5  NAPS2.Lib/Icons/email_setting.png  [F]  <- FatCow_Icons32x32/email_setting.png
2a8b045657fc840a119466cbdac4936ef364a8d133609d8ab5cc4a09d5bb4ae8  NAPS2.Lib/Icons/exclamation-small.png  [F]  <- FatCow_Icons16x16/exclamation.png
ded1bf0150eb52de450b011b2c426a49708f85eefb08eb5ade1c58fd306ab136  NAPS2.Lib/Icons/exclamation.png  [F]  <- FatCow_Icons32x32/exclamation.png
77dd9d833690bfce339a9f424ff770154c34de394116de0df7d2591c98d866f2  NAPS2.Lib/Icons/favicon.ico  [B]
4fb78910d0e286c25d591f22b36ba6169e3c06dbda863bb7aab49a52c3170479  NAPS2.Lib/Icons/file_extension_pdf-hires.png  [H]
97142ba76871f1b9528ac70d35efd026005e61a0594304cc5bcb0fa9ca072d8b  NAPS2.Lib/Icons/file_extension_pdf.png  [R]  <- FatCow_Icons32x32/file_extension_pdf.png
307d5bd804ab9f2fed54815a241cc289ed3ca46b77437b73153720e94bf8fc87  NAPS2.Lib/Icons/file_extension_pdf_small.png  [F]  <- FatCow_Icons16x16/file_extension_pdf.png
9568f9cc56c547d4aa67cd64201d723d7075ba600169efeeba118d708fd4ac96  NAPS2.Lib/Icons/folder_picture-hires.png  [H]
4a5d59d35576728f317b98b1d2206dc6bb9501f116f9fb89dc7ad6561020c0df  NAPS2.Lib/Icons/folder_picture.png  [F]  <- FatCow_Icons32x32/folder_picture.png
8a1c028eb91315c71ca19f53cfecc4b152902d401b0cc9ecf819f5b227e4001a  NAPS2.Lib/Icons/gmail-hires.png  [M]
e8b5a6e8a11ec2655b9b537d84b94185bc64a4e74124662f05fb3f746e924b8f  NAPS2.Lib/Icons/gmail.png  [M]
c83fabe32bc5e524a5817cf869ec375ce78b3fe35a88dc18d9f4b8cf5288a66b  NAPS2.Lib/Icons/help-small.png  [F]  <- FatCow_Icons16x16/help.png
f56a2cace606852dfb13bcbbc0ca3fecd9d8af17a32274247389a2574651d739  NAPS2.Lib/Icons/hourglass_grey.png  [O]
a58cefbf74621d02eec56c64c36f594dbc2d9325f3bbf3db32c4a76a2f862d18  NAPS2.Lib/Icons/information-small.png  [F]  <- FatCow_Icons16x16/information.png
67d05c80c87ef9e84b9c030aacc60d94c1102c0de14bc43a70c4f094c627196d  NAPS2.Lib/Icons/information.png  [R]  <- FatCow_Icons32x32/information.png
11e55ce68558b4b7284ffce9ec3d769c1618968272a080fcffa015ae03eacdaa  NAPS2.Lib/Icons/key-small.png  [F]  <- FatCow_Icons16x16/key.png
a2ad30b6a6951434a49a550a8aea358068c75b09cf555c5e15fb611338c4cb5a  NAPS2.Lib/Icons/key.png  [F]  <- FatCow_Icons32x32/key.png
36447b6a5ed8f3dfe7d78b0932200fd30dedfd32fce831486a604d5b95198af9  NAPS2.Lib/Icons/keyboard-small.png  [F]  <- FatCow_Icons16x16/keyboard.png
dac231e2cfc1ee06ae87e2f13686ad2e99b66aeb659f07d6cb68201b79dc7b51  NAPS2.Lib/Icons/keyboard.png  [F]  <- FatCow_Icons32x32/keyboard.png
0ab8a21a433128ba0e49848756241fa5d7fadd1e9a476e1c5df79e0499468881  NAPS2.Lib/Icons/large_tiles-small.png  [F]  <- FatCow_Icons16x16/large_tiles.png
764d4cd8f68b48c56ac6c752e81c0279ce9028bea103daff329fccc324348be0  NAPS2.Lib/Icons/large_tiles.png  [F]  <- FatCow_Icons32x32/large_tiles.png
9c43fad6cb3c9b104a16c52d5788fd01f2fc0dfd7c914afe573d301d725cd18f  NAPS2.Lib/Icons/mail_yellow-hires.png  [O]
2f1a23b4aaec2eb8d62429f8732b4941da39abcef6f5be98f95fb7614afd35b2  NAPS2.Lib/Icons/mail_yellow.png  [F]  <- FatCow_Icons32x32/mail_yellow.png
db3ddc1cf06932c9e9d4aa1c8c8ce4683c9375317609eba1566224b165c7d51c  NAPS2.Lib/Icons/network_ip-hires.png  [H]
5869e9a8a782399cd6713ed30222b1b5cb0378f52c8edd58d0a27a8f194971bf  NAPS2.Lib/Icons/network_ip-small.png  [F]  <- FatCow_Icons16x16/network_ip.png
1d7db14402a0f6da56f52b45065ea4a482343dc3861134af85d50c0ae0dfee63  NAPS2.Lib/Icons/network_ip.png  [F]  <- FatCow_Icons32x32/network_ip.png
f7b5379a2735a520fa2549c845ff9fc00d56d0b41178c216e826bd0e3413d526  NAPS2.Lib/Icons/outlooknew-hires.png  [M]
ca38df6c47191cd2ff90ede72b9b16801cafca065f3fadb52fe244a9ebd82841  NAPS2.Lib/Icons/outlooknew.png  [M]
b12013347b5e5644feeb3b3b24f6cea09ce99eccab6230855d2b607a183dafa9  NAPS2.Lib/Icons/outlookweb-hires.png  [M]
752c76e7ef23460d0b52d3290c55d9b143fda80c648343bd5fab513c7e9c4b12  NAPS2.Lib/Icons/outlookweb.png  [M]
114d1b3e1b8196c085ae5c7d0ef504d6fdf12fd831cc144381abb78e0021f733  NAPS2.Lib/Icons/paste-small.png  [F]  <- FatCow_Icons16x16/paste_plain.png
5d11f6a2fc13ee066b4292a6198b02c462a54674c1d9eadb9dc35db60bcfed56  NAPS2.Lib/Icons/paste.png  [F]  <- FatCow_Icons32x32/paste_plain.png
2564eb7b60a4b7eb05508dd37b0de2ee7f260774b4d672b744e0059351b47fa1  NAPS2.Lib/Icons/pencil-small.png  [F]  <- FatCow_Icons16x16/pencil.png
9e0ca7b8858354e3d5fd9b03159176e743a8d0a0310187beabe3ca62c4d02d0b  NAPS2.Lib/Icons/pencil.png  [F]  <- FatCow_Icons32x32/pencil.png
1a285987b963e0c9d5eed1b6c406b11a7d43bf8486075cf460e998a256671417  NAPS2.Lib/Icons/picture-small.png  [F]  <- FatCow_Icons16x16/picture.png
43d7931a428bd31e10007d33cda15033eff3633717e82f7918244e591262e618  NAPS2.Lib/Icons/picture.png  [R]  <- FatCow_Icons32x32/picture.png
ce1e89d88543521fb8c93fc2d2721389304118a61048a7d430efde6016e89fcf  NAPS2.Lib/Icons/picture_edit-hires.png  [H]
035deb2e7124ea3893ec1c29e0900ac763ab86ab007389467ff717e84f764336  NAPS2.Lib/Icons/picture_edit.png  [F]  <- FatCow_Icons32x32/picture_edit.png
adc29ed90c02a93cad408f0be0776e6af26f1a219a0b587b32463d6ca312a456  NAPS2.Lib/Icons/pictures-hires.png  [H]
4d8053ff7a2c3e8b48e9d9e728c2dd4369df07b794c2019bf3b855da8eac03eb  NAPS2.Lib/Icons/pictures.png  [F]  <- FatCow_Icons32x32/pictures.png
0d90ec9585f1bfb49b7c44a1795155febc446cfac91a6b7763e4de209f6ed63b  NAPS2.Lib/Icons/printer-hires.png  [H]
c133b31a564af53b6e831db333a6107ce8bdb844e773b7dbbf71f2931f0f2c2f  NAPS2.Lib/Icons/printer.png  [F]  <- FatCow_Icons32x32/printer.png
a5648253487a4072fb1a3e94b356cce9375e9a820e69b5dbdbb80fede4db7eae  NAPS2.Lib/Icons/redo-small.png  [F]  <- FatCow_Icons16x16/redo.png
f2435dc846c23de366339d82981ebb4b85b69496b233c197b17196f5919483a1  NAPS2.Lib/Icons/redo.png  [F]  <- FatCow_Icons32x32/redo.png
9ba55ccd393451c765f251a4d6814a29673611ce3a88f84f8219a22d54624e18  NAPS2.Lib/Icons/scanner-128.png  [B]
943eddb7676854aec2d03a372c13002f66c18504651f4195ea2ea628090053b4  NAPS2.Lib/Icons/scanner-16-rev2.png  [B]
e1f8b5eac5d710baccd8aeefd8a3dcb6323874c15fdcfa537899a595918f7391  NAPS2.Lib/Icons/scanner-32-gray.png  [B]
fe20c99efa89f3efab24b9b9bb6b5afa70da85a6a483fdfff66abf7afb9657b8  NAPS2.Lib/Icons/scanner-32-rev2.png  [B]
a3981062c649fb28c90d554fd1af72af8b4c7db2e3d3c547a7f2798ad897a772  NAPS2.Lib/Icons/scanner-48-rev2.png  [B]
9bbe3e82d6825247a5fbd5745905ed49fd221d663d690e1185a351df5a9f21ad  NAPS2.Lib/Icons/scanner-64-rev2.png  [B]
66bef4f1d9c8f60d65e8c9085dc201d2eabb9819dd4ebed32f04a14f0a6ef642  NAPS2.Lib/Icons/scanner-96.png  [B]
d28252c095f2f35a106ca4db478bda2c483dc69ca3a6111208d2e8beb73baf82  NAPS2.Lib/Icons/scanner-default-hires.png  [B]
6916e262c848d3fe5213023866788832032a0852f2ce078722a153b88b992695  NAPS2.Lib/Icons/scanner-default-rev2.png  [B]
ed19c99ebcbf7724eaae569b5d6d16b7ba81d0b5ca09d87a3ec48e287a3dc4d4  NAPS2.Lib/Icons/scanner-lock-default-hires.png  [B]
209450b5a487d0536bfbfdb345cab1cb14c38126399fe24327da015a5ed3e07c  NAPS2.Lib/Icons/scanner-lock-default-rev2.png  [B]
b2573b5e5cac635fe4e430fab7f1e63ca5fc760645d749f1368337afe121f5eb  NAPS2.Lib/Icons/scanner-lock-hires.png  [B]
3d40951c3bd10e35d2ee74b645c661fa5ab1e4c9323802c6e5e72e8936d78699  NAPS2.Lib/Icons/scanner-lock-rev2.png  [B]
26cfe70bbc68fb6abdcec426274f667e7aaf22e921242682eff37368b59d4c56  NAPS2.Lib/Icons/scanner-wireless-hires.png  [B]
5db7e7d76e615673e82917cd54a5ff06c1aec639c057854405101a70c9d9c02e  NAPS2.Lib/Icons/scanner-wireless-rev2.png  [B]
1ee029daf81ca30c6912936f235de6fada2b061533ed4c8e1d0501d7440798c1  NAPS2.Lib/Icons/shape_align_bottom-small.png  [F]  <- FatCow_Icons16x16/shape_align_bottom.png
ea7e1a978029e222526662d9823e260661b932547fd13aa58171baf8c1794d5d  NAPS2.Lib/Icons/shape_align_bottom.png  [F]  <- FatCow_Icons32x32/shape_align_bottom.png
2854d2f793c369f8785c6bab4b225f2bfa30f134dfb59fa8fce3bffc343f8ced  NAPS2.Lib/Icons/shape_align_center-small.png  [F]  <- FatCow_Icons16x16/shape_align_center.png
dc4f90045953654ef91a495b878cd0510c48993d518550b656990cdfb450523e  NAPS2.Lib/Icons/shape_align_center.png  [F]  <- FatCow_Icons32x32/shape_align_center.png
73e94d048403fd0c9c27b96354fc6e31a9a2385eac1cdd048950f2444b871995  NAPS2.Lib/Icons/shape_align_left-small.png  [F]  <- FatCow_Icons16x16/shape_align_left.png
0c85940d82488d086212ff866198026963457ba761815ba766c25204c096af82  NAPS2.Lib/Icons/shape_align_left.png  [F]  <- FatCow_Icons32x32/shape_align_left.png
118136bb552de12677b21aa5a0584ba7decacd6b5528391ad2629a2cfb310e81  NAPS2.Lib/Icons/shape_align_middle-small.png  [F]  <- FatCow_Icons16x16/shape_align_middle.png
eb9e8ea2474816dbe2ba6d0a547fdf2cdcf3cf6146a9cf05a3e7eeadd0270396  NAPS2.Lib/Icons/shape_align_middle.png  [F]  <- FatCow_Icons32x32/shape_align_middle.png
a455ab800830d175b463bb3c0eff35951b3391f539623280b7ee60e5803f62d6  NAPS2.Lib/Icons/shape_align_right-small.png  [F]  <- FatCow_Icons16x16/shape_align_right.png
9747cb7bc7e6982afd91d4b3a462f1de839b3690d8ded6a957b87d8d12dbfd0b  NAPS2.Lib/Icons/shape_align_right.png  [F]  <- FatCow_Icons32x32/shape_align_right.png
9156ffac2303e327f71fd167558d1f2ab01b59803ab87f350daa651fcff488d9  NAPS2.Lib/Icons/shape_align_top-small.png  [F]  <- FatCow_Icons16x16/shape_align_top.png
afc882d72ff06173382c4495cc1ffea43e9e829d86586d877b2647d48b97eca6  NAPS2.Lib/Icons/shape_align_top.png  [F]  <- FatCow_Icons32x32/shape_align_top.png
c8bb69a288f6085f0e07f2573967d11ec3a8f10c838379851bba8d6ab7367074  NAPS2.Lib/Icons/sharpen-small.png  [F]  <- FatCow_Icons16x16/sharpen.png
ff6388311aacab7a66ece95480002bbb09623f2ff41129c30247a203cff28ad0  NAPS2.Lib/Icons/sharpen.png  [F]  <- FatCow_Icons32x32/sharpen.png
ac78f9c0b4c7d24572c5d2f382f6c35e969012c22963b3b8e2bd5092d922c4a9  NAPS2.Lib/Icons/split-small.png  [F]  <- FatCow_Icons16x16/splitter.png
e624b876873afdcecb557f23468f83013f9ef975ff17984ff94e6174928d4ec5  NAPS2.Lib/Icons/split.png  [F]  <- FatCow_Icons32x32/splitter.png
8e0bce343cca48ae9ed48a0fb574100dbc302f9a13ed94b96ee71725b57b87e6  NAPS2.Lib/Icons/split_hor-small.png  [F]  <- FatCow_Icons16x16/splitter_horizontal.png
3d3ecd7ab7a00a0c5fcd751e4fdcff1b54cfb101ec700292a211fa51bd99e2e8  NAPS2.Lib/Icons/split_hor.png  [F]  <- FatCow_Icons32x32/splitter_horizontal.png
fc5af91f1abaac83e1704c1db4cd67897282db33f932839e0cf787a09f75c7d0  NAPS2.Lib/Icons/spring-small.png  [F]  <- FatCow_Icons16x16/spring.png
e3cf3ffc583308240621fc644440533c699ce1cdc221c47f184cf639519898bb  NAPS2.Lib/Icons/spring.png  [F]  <- FatCow_Icons32x32/spring.png
d5a372dd7a1239edbce0e3f06977a0b2dc04f992ad488541d8b8f3571bf1c3c8  NAPS2.Lib/Icons/switch-small.png  [O]
50c3d94746171cb458481d13598b1c472549a010b1020efb4d8d13d4cdea0cf4  NAPS2.Lib/Icons/switch.png  [O]
e88aee4e2433395482a593eb0411288c22ca78067f8fdd3c1e5ece2c81524077  NAPS2.Lib/Icons/switch_hor-small.png  [O]
8025bc0d583634d39d5a8720584d8db4ddaf6a58a7fe8289c75fa55b41db0fc8  NAPS2.Lib/Icons/switch_hor.png  [O]
ecf801b851e3980f27ff7b40fb5553812f60690d00b6903719b6c900a9317dac  NAPS2.Lib/Icons/text-hires.png  [H]
979a1ccfbfc4cf02e4dec1a716571037a4d4c95a216216771c39529020a1e48b  NAPS2.Lib/Icons/text-small.png  [F]  <- FatCow_Icons16x16/text.png
a514ea3356032fb4fb613f1311b30914a477cc7e1815ccbe47293e73d3ccc0c8  NAPS2.Lib/Icons/text.png  [F]  <- FatCow_Icons32x32/text.png
62abe3df4fd6c96ebce7c70ddb1ad89a3337ce1a5ff1f7bb9cebd26f9c314a81  NAPS2.Lib/Icons/text_align_justify-small.png  [F]  <- FatCow_Icons16x16/text_align_justity.png
0c93da742cb1cdd6e69cbdd37d1501202118fbae9d0297bbb9743e050a46f3f0  NAPS2.Lib/Icons/text_align_justify.png  [F]  <- FatCow_Icons32x32/text_align_justity.png
737ed8f51a0db101ce30db55bfe8be30a09b7e595c45f015dac5a03398a93758  NAPS2.Lib/Icons/thunderbird-hires.png  [M]
1f3b939b1d356958b7d1a40830ec9780a8d249a1b04a17fb80b65162f02b7626  NAPS2.Lib/Icons/thunderbird.png  [M]
88af95df19b8ddffcbe63b38457ac039725b85373d3039ad5393e6503a936b0a  NAPS2.Lib/Icons/tick-small.png  [F]  <- FatCow_Icons16x16/tick.png
db0179654313473577ae3605e1aef538ae23cd46e5e1b14ea897aa1d112cfbd0  NAPS2.Lib/Icons/tick.png  [F]  <- FatCow_Icons32x32/tick.png
fd07f7bc56bc91e251c45e640646c27a9e9c146d7b36471184f3d5dbc0fca1f2  NAPS2.Lib/Icons/transform_crop-small.png  [F]  <- FatCow_Icons16x16/transform_crop.png
8ee3b794983248699a7710abd3570be15567a219a7b08a0f5c48ed1ee025ebe2  NAPS2.Lib/Icons/transform_crop.png  [F]  <- FatCow_Icons32x32/transform_crop.png
edd7e56747525dee4740ed19bdc60f043bd38155eeb1c40fd23f7c34495e37b4  NAPS2.Lib/Icons/undo-small.png  [F]  <- FatCow_Icons16x16/undo.png
5e4b154f774f1697edd943ac7013263d2231d214d41e518fe632c24b875f6008  NAPS2.Lib/Icons/undo.png  [F]  <- FatCow_Icons32x32/undo.png
2d049effef3a7733fb95e1ad7ed205b6ed777ff75f92de0344a557be596e16aa  NAPS2.Lib/Icons/weather_sun-small.png  [O]
eb0756d9b8c437336a39d733803e71ba8f921388cc979e0d6c8c8b0fc181e239  NAPS2.Lib/Icons/weather_sun.png  [F]  <- FatCow_Icons32x32/weather_sun.png
882f21fbdb00536e019ad6e402af5db1f63209d6585d26f3b150cc87c207362b  NAPS2.Lib/Icons/wireless-small.png  [O]
6325381cf6f0dccdea2064fa1d7f5279f6a9e127c1f3d67fbc58640cbd3f9468  NAPS2.Lib/Icons/wireless.png  [O]
4bc9e192c1f08d4197dcd65ba00a9639767181c77255729e6ae55a0331680eeb  NAPS2.Lib/Icons/world-hires.png  [H]
c129f5232be156507fa3a4c94823678de45d41f32203e663c41bdd3a58f08097  NAPS2.Lib/Icons/world.png  [F]  <- FatCow_Icons32x32/world.png
912abe6f62e51c4f7431663b8f09fabd254461af44ab7ab10c6e790d20a0e4c7  NAPS2.Lib/Icons/zoom-small.png  [F]  <- FatCow_Icons16x16/zoom.png
cb5559c81922f0b5708c585e0463c191ebf9d2c5f579715d26b3a1f32964615b  NAPS2.Lib/Icons/zoom.png  [F]  <- FatCow_Icons32x32/zoom.png
0551e7b917477c59d91b3cb30f65bf676e8f3c6253da6f76a81e2d42ba05c5e7  NAPS2.Lib/Icons/zoom_actual-small.png  [F]  <- FatCow_Icons16x16/zoom_actual.png
1d50e0639254e930c329afa3c6b0df92590d54d4fa3fa62a4e521085793da338  NAPS2.Lib/Icons/zoom_actual.png  [F]  <- FatCow_Icons32x32/zoom_actual.png
d3e8d5f054f2ec3da639299201d930b95baa85175b6d5d4ad753a69076d412b2  NAPS2.Lib/Icons/zoom_in-small.png  [R]  <- FatCow_Icons16x16/zoom_in.png
f516ed335aa42a0c4ee1d6ac98c8197dc7fdf09dfe1d3fd3231f59bf855b35f1  NAPS2.Lib/Icons/zoom_in.png  [F]  <- FatCow_Icons32x32/zoom_in.png
a389214dae73fc86e65a9c1c347b7a3e96d7572799c4a0627024bcd56e31c404  NAPS2.Lib/Icons/zoom_out-small.png  [R]  <- FatCow_Icons16x16/zoom_out.png
ac4b8c2dd8854b3ee5da06b9bc0e5f57b7649ea6c8db6844b13ac0014e93a038  NAPS2.Lib/Icons/zoom_out.png  [F]  <- FatCow_Icons32x32/zoom_out.png
```

</details>

Inventargruppen: F=118, R=11, H=18, B=16, M=10, O=15. SHA-256 des reinen, nach Pfad sortierten Inventars (`hash + zwei Leerzeichen + Pfad + LF`): `563cdd482d66a8007bb9a495efd101d81e8ee66c42a67a4c1234f105d8c9def9`.

Nicht referenzierte Quelldateien (unter `NAPS2.Lib/Icons/`): `btn_donate_LG.gif`, `help.png`, `scanner-16-rev0.png`, `scanner-16-rev1.png`, `scanner-32-rev1.png`, `scanner-48-rev1.png`, `scanner-64-rev1.png`, `scanner-72-rev1.png`, `scanner-default-rev1.png`, `scanner-lock-default-rev1.png`, `scanner-lock-rev1.png`, `wireless16_filled.png`, `wireless_filled.png`.
