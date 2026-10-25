#!/usr/bin/env python3
"""Export a clean source kit, local app/DMG and checksums. No push or upload.

Requires a committed clean source checkout and a separately built/verified app.
All outputs are new and outside Git. Existing apps and settings are read only.
Replay the mbox with git am --keep-cr to preserve original CRLF licence bytes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

VERSION = '8.5.1-es60w.1'
PREFIX = 'NAPS2-ES60W-' + VERSION


def sha(f):
    h = hashlib.sha256()
    with f.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app', type=Path, required=True)
    p.add_argument('--downloads', type=Path, required=True)
    p.add_argument('--package-inputs', type=Path, required=True)
    p.add_argument('--source-supplement', type=Path,
        help='Recovered third-party sources matching legal/source-supplement.lock.json')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    here = Path(__file__).resolve().parent
    repo = here.parent
    out = a.output.resolve()
    if out.exists() or repo == out or repo in out.parents:
        p.error('Use a new release directory outside Git')
    status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True)
    if status.strip():
        p.error('Commit the source snapshot before making the source kit')
    supplement_lock = here / 'legal/source-supplement.lock.json'
    if supplement_lock.exists() and not a.source_supplement:
        p.error('This revision requires --source-supplement; do not omit recovered sources')
    tracked = subprocess.check_output(['git', 'ls-files', 'es60w'], cwd=repo, text=True).splitlines()
    generated = [n for n in tracked if any(x in Path(n).parts for x in ['bin', 'obj', '__pycache__'])]
    if generated:
        p.error('Generated verification outputs must not be tracked in release sources')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    out.mkdir(parents=True)
    env = dict(os.environ, COPYFILE_DISABLE='1')
    app = out / 'NAPS2 ES60W.app'
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(a.app.resolve())], check=True)
    subprocess.run(['ditto', str(a.app.resolve()), str(app)], check=True)
    dmg = out / (PREFIX + '-arm64.dmg')
    subprocess.run([sys.executable, str(here / 'tools/make-private-dmg.py'),
        '--app', str(app), '--destination', str(dmg), '--readme', str(here / 'FIRST-START.de.txt'),
        '--volume-name', 'NAPS2 ES60W'], check=True, env=env)
    source_archive = out / (PREFIX + '-sources.tar.gz')
    with tempfile.TemporaryDirectory(prefix='es60w-source-kit-', dir=out.parent) as tmp:
        root = Path(tmp) / (PREFIX + '-sources')
        checkout = root / 'naps2'
        checkout.mkdir(parents=True)
        snapshot = Path(tmp) / 'checkout.tar'
        with snapshot.open('wb') as stream:
            subprocess.run(['git', 'archive', head], cwd=repo, stdout=stream, check=True)
        with tarfile.open(snapshot) as tar:
            tar.extractall(checkout)
        dependencies = root / 'dependencies'
        dependencies.mkdir()
        lock = json.loads((here / 'sources.lock.json').read_text())
        for e in lock:
            f = a.downloads.resolve() / e['filename']
            if sha(f) != e['sha256']:
                raise RuntimeError('Source archive changed: ' + e['name'])
            shutil.copy2(f, dependencies / f.name)
        inputs = a.package_inputs.resolve()
        inventory = json.loads((inputs / 'MANIFEST.json').read_text())
        for e in inventory['packages']:
            f = inputs / e['build_input']
            if not f.resolve().is_relative_to(inputs) or sha(f) != e['sha256']:
                raise RuntimeError('Package input changed')
            e = e.get('declared_source', {})
            if 'archive' in e:
                f = inputs / e['archive']
                if not f.resolve().is_relative_to(inputs) or sha(f) != e['sha256']:
                    raise RuntimeError('Declared source changed')
        shutil.copytree(inputs, root / 'package-inputs')
        source_files = {str(f.relative_to(checkout)): sha(f) for f in checkout.rglob('*')
                        if f.is_file() and not f.is_symlink()}
        manifest = {'release': VERSION, 'naps2_base': '3481963789af647a9f9e0a19176a0d2f7f593b5d',
            'source_head': head, 'source_files_sha256': source_files,
            'native_source_archives': lock, 'nuget_build_inputs': len(inventory['packages']),
            'preferred_application_and_free_helper_sources_present': True,
            'third_party_source_closure_verified': False, 'private_history_included': False,
            'no_proprietary_epson_inputs': True, 'public_release_cleared': False}
        (root / 'SOURCE-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
        (root / 'README-build.md').write_text('''# NAPS2 ES60W local source kit

`naps2/` is the complete editable committed application source tree, including
the ES60W helper integration and its build/package/check tools. No private Git
history, proprietary Epson files, credentials or real scans are included.

See `naps2/es60w/README.md`. The three hash-pinned native source archives are
in `dependencies/`; `package-inputs/nuget-feed/` preserves the restored NuGet
build inputs. `package-inputs/declared-sources/` contains the available immutable
repository snapshots declared by package metadata. That metadata and archived
repositories do not prove complete transitive/submodule source closure or
independent reproduction of all bundled libraries. Unresolved cases remain
explicit in `package-inputs/MANIFEST.json` and `naps2/es60w/SOURCE-STATUS.json`.

Build serially with the documented Xcode/.NET/macOS workload and CMake/autotools
prerequisites. Native build installs only to its own new output prefix.

```sh
cd naps2
python3 es60w/build-native.py --downloads ../dependencies --output /NEW/native-build
python3 es60w/build-app.py --native-build /NEW/native-build \\
  --output /NEW/app-build --dotnet /path/to/dotnet
```

For an isolated rebuild, pass `--nuget-source ../package-inputs/nuget-feed` and
`--nuget-packages /NEW/package-cache` to build-app.py.

The complete preferred sources of this application and helper are present;
this local preparation is not yet a cleared public corresponding-source offer.
Do not publish this package until the recorded source/licence/artwork and trusted
signing/first-launch items have been closed. It is ad-hoc signed, not notarized.
''')
        with tarfile.open(source_archive, 'w:gz', compresslevel=6) as tar:
            tar.add(root, arcname=root.name)
    mbox = out / (PREFIX + '-changes.mbox')
    with mbox.open('wb') as stream:
        subprocess.run(['git', 'format-patch', '--stdout', '--no-signature',
            '3481963789af647a9f9e0a19176a0d2f7f593b5d..' + head], cwd=repo, stdout=stream, check=True)
    hashes = {f.name: sha(f) for f in [dmg, source_archive, mbox]}
    if supplement_lock.exists():
        supplemental_archive = out / (PREFIX + '-third-party-sources.tar.gz')
        root = a.source_supplement.resolve(strict=True)
        recovered = json.loads(supplement_lock.read_text())
        with tarfile.open(supplemental_archive, 'w:gz', compresslevel=6) as tar:
            tar.add(supplement_lock, arcname='third-party-sources/source-supplement.lock.json')
            for r in recovered['sources']:
                f = root / r['file']
                if not f.resolve().is_relative_to(root) or sha(f) != r['sha256']:
                    raise RuntimeError('Recovered third-party source missing or changed')
                tar.add(f, arcname='third-party-sources/' + r['file'])
        hashes[supplemental_archive.name] = sha(supplemental_archive)
    (out / 'SHA256SUMS').write_text(''.join(h + '  ' + n + '\n' for n, h in hashes.items()))
    (out / 'RELEASE-MANIFEST.json').write_text(json.dumps({'version': VERSION,
        'branch': 'es60w-macos-release', 'source_head': head, 'artifacts_sha256': hashes,
        'architecture': 'arm64', 'developer_id_signed': False, 'notarized': False,
        'public_release_cleared': False, 'new_physical_scans': 0,
        'installed_working_app_changed': False}, indent=2) + '\n')
    shutil.copy2(here / 'FIRST-START.de.txt', out / 'FIRST-START.de.txt')
    print('Local app, DMG, source kit, patch series and SHA256SUMS prepared', flush=True)


if __name__ == '__main__':
    main()
