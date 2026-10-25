#!/usr/bin/env python3
"""Fetch the documented free-source supplement into a new local directory.

No downloaded code is executed. Checksums pin the retained evidence; source
correspondence levels and unresolved cases remain in the lock file.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
out = a.output.resolve()
if out.exists():
    p.error('Use a new output directory')
out.mkdir(parents=True)
lock = Path(__file__).resolve().with_name('source-supplement.lock.json')
records = json.loads(lock.read_text())
for r in records['sources']:
    target = out / r['file']
    if not target.resolve().is_relative_to(out):
        raise RuntimeError('Unsafe output path')
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
        '--max-time', '180', r['url'], '-o', str(target)], check=True)
    h = hashlib.sha256()
    with target.open('rb') as stream:
        for b in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(b)
    if h.hexdigest() != r['sha256']:
        raise RuntimeError('Source evidence checksum mismatch: ' + target.name)
    print(target.name + ': verified', flush=True)
(out / 'source-supplement.lock.json').write_text(lock.read_text())
