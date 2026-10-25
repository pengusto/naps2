# NAPS2 ES60W 8.5.1-es60w.1 — lokaler Release-Entwurf

Ein App-Paket mit NAPS2 und freiem SANE/epsonds-Scanhelfer für einen ES-60W über
USB auf Apple Silicon. .NET, libusb und JPEG sind mitgeliefert; der Nutzer benötigt
keinen Epson- oder Homebrew-Installer. DMG öffnen, App nach Programme ziehen,
öffnen und Scannen wählen. Vorhandene Apps nicht überschreiben.

300 dpi/Farbe/automatischer Zuschnitt sind voreingestellt. Jede neue Aufnahme
wird als PDF in Dokumente/Scans abgelegt. Die Scannertaste kann im Scan-Menü pro
Sitzung aktiviert werden. Paperless ist unabhängig und hier nicht eingerichtet.
WLAN, Intel und universelle Epson-Unterstützung gehören nicht zu diesem Paket.

Die 24 App-Quelländerungen der bestehenden Lösung sind in diesem Branch enthalten.
Der Helfer wird zusammen mit passenden libusb-/JPEG-Quellen neu gebaut. Die App
wird vollständig mit statischem macOS-Registrar kompiliert. Paketwerkzeuge prüfen
Signaturintegrität, entfernen lokale Build-RPATHs und vermeiden persönliche Debugpfade und liefern die
Quellenarchive und SHA256SUMS getrennt von der DMG. Keine privaten Scans oder
proprietären Epson-Dateien gehören in eines der Artefakte.

Der neue Build wird ausschließlich per Software geprüft; kein neuer echter Scan
und kein neuer Hardware-/Millimeternachweis. Bestehende akzeptierte Scans sind
Nachweise der bisherigen Installation. Die installierte funktionierende App und
ihre Einstellungen bleiben erhalten.

Ad-hoc-signiert, nicht Developer-ID-signiert oder Apple-notarisiert. Beim ersten
Öffnen kann eine manuelle macOS-Freigabe nötig sein. Regulärer quarantänisierter
Finder-Erststart und Ziel-Mac-USB wurden für diesen neuen Build nicht bestätigt.

Der Quellensatz enthält die vollständige editierbare App, die freien Helferquellen,
Build-/Paketwerkzeuge und die aufgelösten Buildpakete. Verfügbare unveränderliche
Drittanbieter-Quellstände werden mit Herkunft und Prüfsumme aufbewahrt. Bei noch
nicht vollständig geklärten Unterquellen und Grafikrechten bleibt der Status
ausdrücklich offen. Dieser lokale Entwurf ist keine öffentliche Releasefreigabe.
