#!/usr/bin/env python3
"""Preserve resolved NuGet build inputs and immutable declared repository snapshots.

This is a build inventory, not proof of corresponding-source closure. Repository
metadata does not prove independent reproduction of a binary or its submodules.
Only source archives are downloaded; no downloaded code is executed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--assets', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--cache', type=Path, help='Reuse only verified immutable archives from a prior inventory')
a = p.parse_args()
out = a.output.resolve()
if out.exists():
    p.error('Output must be a new directory')
out.mkdir(parents=True)
(out / 'nuget-feed').mkdir()
(out / 'declared-sources').mkdir()
assets = json.loads(a.assets.read_text())
roots = [Path(x) for x in assets['packageFolders']]
framework_lock = Path(__file__).resolve().parent / 'framework-downloads.lock.json'
if framework_lock.exists():
    for e in json.loads(framework_lock.read_text()):
        version = e['version'].strip('[]').split(',')[0].strip()
        assets['libraries'].setdefault(e['name'] + '/' + version, {
            'type': 'package', 'path': e['name'].lower() + '/' + version,
            'build_input_kind': 'runtime or targeting download'})
records, source_cache = [], {}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

if a.cache:
    cached = json.loads((a.cache / 'MANIFEST.json').read_text())
    for row in cached['packages']:
        src = row.get('declared_source', {})
        declared = row.get('declared_repository', {})
        if 'archive' not in src or not declared.get('commit'):
            continue
        f = a.cache / src['archive']
        if not f.resolve().is_relative_to(a.cache.resolve()) or sha(f) != src['sha256']:
            raise RuntimeError('Invalid archive cache')
        dest = out / src['archive']
        if not dest.exists():
            shutil.copy2(f, dest)
        repo = urllib.parse.urlsplit(declared['url']).path.strip('/').removesuffix('.git')
        source_cache[repo + '@' + declared['commit']] = src

for key, v in assets['libraries'].items():
    if v['type'] != 'package':
        continue
    folder = next((r / v['path'] for r in roots if (r / v['path']).is_dir()), None)
    if not folder:
        raise RuntimeError('Resolved package missing: ' + key)
    package = next(folder.glob('*.nupkg'))
    dest = out / 'nuget-feed' / package.name
    shutil.copy2(package, dest)
    spec = next(folder.glob('*.nuspec'))
    metadata = next(x for x in ET.parse(spec).getroot() if x.tag.split('}')[-1] == 'metadata')
    repository = next((x for x in metadata if x.tag.split('}')[-1] == 'repository'), None)
    declared = repository.attrib if repository is not None else {}
    row = {'package': key, 'build_input': 'nuget-feed/' + dest.name,
           'sha256': sha(dest), 'declared_repository': declared,
           'source_status': 'not resolved', 'independently_rebuilt': False,
           'shipped_in_app': 'not inferred from restore inventory'}
    url = urllib.parse.urlsplit(declared.get('url', ''))
    commit = declared.get('commit', '')
    parts = url.path.strip('/').removesuffix('.git').split('/')
    if url.hostname == 'github.com' and len(parts) == 2 and re.fullmatch('[a-fA-F0-9]{40}', commit):
        repo = '/'.join(parts)
        source_key = repo + '@' + commit
        if source_key not in source_cache:
            name = repo.replace('/', '--') + '-' + commit + '.tar.gz'
            target = out / 'declared-sources' / name
            source_url = 'https://codeload.github.com/' + repo + '/tar.gz/' + commit
            r = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                '--max-time', '180', '--retry', '1', source_url, '-o', str(target)],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if r.returncode:
                target.unlink(missing_ok=True)
                source_cache[source_key] = {'url': source_url, 'error': 'source download failed'}
            else:
                source_cache[source_key] = {'url': source_url,
                    'archive': 'declared-sources/' + name, 'sha256': sha(target)}
        row['declared_source'] = source_cache[source_key]
        if 'archive' in row['declared_source']:
            row['source_status'] = 'declared immutable repository archived; submodule/transitive closure unverified'
    records.append(row)
    print(key + ': ' + row['source_status'], flush=True)
    (out / 'MANIFEST.json').write_text(json.dumps({'packages': records,
        'complete_third_party_source_closure_verified': False,
        'no_proprietary_epson_input': True}, indent=2) + '\n')
print('Resolved package inputs preserved: ' + str(len(records)), flush=True)
