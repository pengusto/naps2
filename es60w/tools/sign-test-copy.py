#!/usr/bin/env python3
"""Copy and locally sign a complete NAPS2 build; never modify the build/original app."""
import argparse
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source_app', type=Path)
p.add_argument('destination_app', type=Path)
p.add_argument('entitlements', type=Path)
a = p.parse_args()
source, dest = a.source_app.resolve(), a.destination_app.resolve()
if dest.exists() or source == dest or not (source / 'Contents/MacOS/NAPS2').is_file():
    p.error('Use a complete source build and a NEW destination .app path')
if dest.suffix != '.app' or not a.entitlements.is_file():
    p.error('A .app destination and upstream Entitlements.plist are required')
subprocess.run(['ditto', str(source), str(dest)], check=True)
# --deep alone does not reliably sign MonoBundle libraries: sign native files explicitly.
native = []
for f in sorted(dest.rglob('*')):
    if f.is_symlink() or not f.is_file():
        continue
    with f.open('rb') as stream:
        magic = stream.read(4)
    if magic in (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'):
        native.append(f)
main = dest / 'Contents/MacOS/NAPS2'
for f in native:
    if f != main:
        subprocess.run(['codesign', '--force', '--sign', '-', '--options', '0', str(f)], check=True, capture_output=True)
# Nested code bundles must be sealed after their native members and before the outer app.
for bundle in sorted(dest.rglob('*.bundle'), key=lambda p: len(p.parts), reverse=True):
    subprocess.run(['codesign', '--force', '--sign', '-', '--options', '0', str(bundle)],
                   check=True, capture_output=True)
subprocess.run(['codesign', '--force', '--sign', '-', '--options', '0', '--entitlements', str(a.entitlements.resolve()), str(dest)], check=True)
for f in native:
    subprocess.run(['codesign', '--verify', '--strict', str(f)], check=True)
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(dest)], check=True)
print(f'Locally signed and verified {len(native)} native files: {dest}')
print('Local test build only; no notarization or hardware validation.')
