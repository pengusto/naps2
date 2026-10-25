#!/usr/bin/env python3
"""Static install-input audit. No app, helper, driver or device is executed."""
import argparse
import json
import re
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--app', type=Path, required=True)
p.add_argument('--output', type=Path, required=True, help='NEW JSON outside Git')
a = p.parse_args()
app = a.app.resolve(strict=True)
if a.output.exists() or any((d / '.git').exists() for d in [a.output.parent, *a.output.parents]):
    p.error('Requires a new output outside Git')
rows = []
for f in sorted(app.rglob('*')):
    if not f.is_file() or f.is_symlink(): continue
    with f.open('rb') as stream: magic = stream.read(4)
    if magic not in (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'): continue
    links = subprocess.check_output(['otool', '-L', str(f)], text=True).splitlines()[1:]
    # otool -L also lists LC_ID_DYLIB. A dylib's own relative ID is not a dependency.
    ids = [line.strip() for line in subprocess.check_output(['otool', '-D', str(f)], text=True).splitlines()[1:]]
    deps = [line.strip().split(' (compatibility')[0] for line in links]
    deps = [link for link in deps if link not in ids]
    bad = [link for link in deps if not link.startswith(('@loader_path/', '@rpath/', '@executable_path/', '/usr/lib/', '/System/Library/'))]
    if bad: raise RuntimeError(f'External dependency in {f}: {bad}')
    commands = subprocess.check_output(['otool', '-l', str(f)], text=True)
    rpaths = re.findall(r'cmd LC_RPATH\n.*?\n\s*path (.+?) \(offset', commands)
    bad = [p for p in rpaths if p.startswith('/') and not p.startswith(('/usr/lib/', '/System/Library/'))]
    if bad: raise RuntimeError('External RPATH in ' + str(f.relative_to(app)) + ': ' + str(bad))
    rows.append(dict(file=str(f.relative_to(app)), install_ids=ids, dependencies=deps, rpaths=rpaths))
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(dict(macho_files=len(rows), absolute_non_system_dependencies=0, hardware_commands=0)))
