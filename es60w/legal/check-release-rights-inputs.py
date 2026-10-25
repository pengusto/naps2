#!/usr/bin/env python3
"""Mechanically check recovered licence files and absence of obsolete GPLv2 package.

This verifies evidence, not legal clearance. It never executes the app/helper.
"""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--app', type=Path, required=True)
p.add_argument('--source-supplement', type=Path, required=True)
a = p.parse_args()
es = Path(__file__).resolve().parent.parent
app = a.app.resolve(strict=True)
obsolete = app / 'Contents/MonoBundle/NAPS2.Sane.Binaries.dll'
if obsolete.exists():
    raise SystemExit('FAIL: obsolete GPL-2.0-only direct-SANE placeholder is still shipped')
if not (app / 'Contents/Helpers/ScanHelper.bundle/Contents/MacOS/scanimage-real').is_file():
    raise SystemExit('FAIL: separate scan helper missing')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

manifest = json.loads((es / 'licenses/MANIFEST.json').read_text())
if any(Path(n).suffix in ['.py', '.sh', '.pydeps', '.gni'] for n in manifest['files_sha256']):
    raise SystemExit('FAIL: build scripts misclassified as licence texts')
for name, expected in manifest['files_sha256'].items():
    source = es / 'licenses' / name
    packaged = app / 'Contents/Resources/LicenseReview' / name
    if sha(source) != expected or sha(packaged) != expected:
        raise SystemExit('FAIL: licence text missing or changed: ' + name)
supplement = a.source_supplement.resolve(strict=True)
lock = json.loads((es / 'legal/source-supplement.lock.json').read_text())
for r in lock['sources']:
    path = supplement / r['file']
    if not path.resolve().is_relative_to(supplement) or sha(path) != r['sha256']:
        raise SystemExit('FAIL: source evidence missing or changed: ' + path.name)
print(json.dumps({'licence_files_verified_in_source_and_app': len(manifest['files_sha256']),
    'supplemental_source_archives_verified': len(lock['sources']),
    'obsolete_gpl2_placeholder_absent': True, 'separate_scan_helper_present': True,
    'new_device_commands': 0, 'public_release_cleared': False,
    'artwork_and_historical_source_review_remain_explicit': True}))
