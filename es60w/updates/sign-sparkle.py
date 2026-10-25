#!/usr/bin/env python3
"""Sign embedded Sparkle code for this ad-hoc development app, inside out.

The upstream distribution signature is verified before staging. At embedding,
Sparkle's installer peers must be signed for the host, as for Embed & Sign in
Xcode. Preserve the XPC services' original entitlements, never sign with --deep.
"""
import argparse
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--app', type=Path, required=True)
a = p.parse_args()
framework = a.app.resolve(strict=True) / 'Contents/Frameworks/Sparkle.framework'
if not framework.is_dir():
    p.error('Sparkle framework missing')
magic = (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca')
for file in framework.rglob('*'):
    if file.is_symlink() or not file.is_file(): continue
    with file.open('rb') as stream: header = stream.read(4)
    if header in magic:
        subprocess.run(['codesign', '--force', '--sign', '-', '--options', '0',
            '--preserve-metadata=entitlements', str(file)], check=True, capture_output=True)
bundles = [f for f in framework.rglob('*') if f.is_dir() and not f.is_symlink()
           and f.suffix in ['.xpc', '.app']]
for bundle in sorted(bundles, key=lambda f: len(f.parts), reverse=True) + [framework]:
    subprocess.run(['codesign', '--force', '--sign', '-', '--options', '0',
        '--preserve-metadata=entitlements', str(bundle)], check=True, capture_output=True)
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(framework)], check=True)
