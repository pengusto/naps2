#!/usr/bin/env python3
"""Make a private read-only drag-and-drop disk image from an already signed app."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--app', type=Path, required=True)
p.add_argument('--destination', type=Path, required=True)
p.add_argument('--readme', type=Path, help='Package-specific first-start instructions')
p.add_argument('--volume-name', default='NAPS2 Free ES60W')
a = p.parse_args(); app = a.app.resolve(); dest = a.destination.resolve()
if dest.exists() or dest.suffix != '.dmg' or not (app / 'Contents/Resources/free-es60w.marker').is_file():
    p.error('A standalone app and a NEW .dmg destination are required')
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
dest.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='naps2-free-dmg-') as t:
    folder = Path(t) / 'image'; folder.mkdir()
    subprocess.run(['ditto', str(app), str(folder / app.name)], check=True)
    (folder / 'Applications').symlink_to('/Applications')
    shutil.copy2(a.readme or Path(__file__).parent / 'defaults/FIRST-START.de.txt', folder / 'Bitte zuerst lesen.txt')
    subprocess.run(['hdiutil', 'create', '-quiet', '-format', 'UDZO', '-volname', a.volume_name,
                    '-srcfolder', str(folder), str(dest)], check=True)
subprocess.run(['hdiutil', 'verify', str(dest)], check=True)
sha = hashlib.sha256(dest.read_bytes()).hexdigest()
dest.with_suffix('.dmg.sha256').write_text(sha + '  ' + dest.name + '\n')
print('Private experimental disk image SHA256: ' + sha)
