# NAPS2 ES60W installieren

[DMG herunterladen](https://github.com/pengusto/naps2/releases/download/es60w-v8.5.1-3/NAPS2-ES60W-8.5.1-es60w.3-arm64.dmg) – für Apple Silicon (M1 und neuer), ES-60W per USB.

1. DMG öffnen und **NAPS2 ES60W.app** nach **Programme** ziehen. Eine funktionierende ältere App behalten und nicht überschreiben.
2. App öffnen. Falls macOS sie blockiert: erst den Start versuchen, dann **Systemeinstellungen → Datenschutz & Sicherheit → Dennoch öffnen**. Die App ist ad-hoc signiert, ohne Apple-Notarisierung. [Apple-Anleitung](https://support.apple.com/de-de/102445). Gatekeeper eingeschaltet lassen.
3. Scanner per USB verbinden, Papier einlegen, **Scannen** anklicken. Voreingestellt: Farbe, 300 dpi, automatischer Zuschnitt. Neue PDFs werden in **Dokumente/Scans** gespeichert.

Es braucht keine zusätzliche Epson-Software, kein Homebrew, kein .NET und keinen eigenen Treiber-Installer. Optional im Scan-Menü die Scannertaste für die laufende Sitzung aktivieren. Die App muss dafür geöffnet bleiben.

Paperless kann später separat angebunden werden. Hier ist kein Konto, Upload oder automatischer Import eingerichtet.

Dies ist eine unabhängige Vorabversion. Ein kleiner dunkler Restsaum kann bei vorsichtigem Zuschnitt bleiben. Die Hardwarefunktion wurde an früheren Ständen geprüft; dieser Neubau hat keinen neuen echten Scan erhalten. USB/ES-60W/Apple Silicon ist der geprüfte Entwicklungsweg; WLAN, Intel und andere Modelle sind nicht abgenommen. Mindestziel macOS 14, Softwaretest auf 26.6.2.

[Quellen, Prüfsummen und Versionshinweise](https://github.com/pengusto/naps2/releases/tag/es60w-v8.5.1-3)
