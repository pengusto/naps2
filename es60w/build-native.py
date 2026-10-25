#!/usr/bin/env python3
"""Build the pinned free helper and both native dependencies, one worker, no install.

Requires Xcode, CMake, autoconf, automake, libtool and pkg-config on PATH.
Destinations must be NEW and outside the checkout. No device command is run.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--downloads', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    here = Path(__file__).resolve().parent
    out = a.output.resolve()
    if out.exists() or here.parent == out or here.parent in out.parents:
        p.error('Use a new output directory outside the checkout')
    out.mkdir(parents=True)
    env = dict(os.environ, MAKEFLAGS='-j1', CMAKE_BUILD_PARALLEL_LEVEL='1',
               MACOSX_DEPLOYMENT_TARGET='14.0', COPYFILE_DISABLE='1')
    prefix = out / 'prefix'
    sources = {}
    stages = {}

    def run(name, cmd, cwd, changes=None):
        with (out / (name + '.log')).open('wb') as log:
            r = subprocess.run(cmd, cwd=cwd, env=dict(env, **(changes or {})),
                               stdout=log, stderr=subprocess.STDOUT)
        stages[name] = r.returncode
        (out / 'stages.json').write_text(json.dumps(stages, indent=2) + '\n')
        print(name + ': ' + str(r.returncode), flush=True)
        if r.returncode:
            raise RuntimeError('See ' + str(out / (name + '.log')))

    entries = json.loads((here / 'sources.lock.json').read_text())
    for e in entries:
        archive = a.downloads.resolve() / e['filename']
        if not archive.exists():
            subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                            e['url'], '-o', str(archive)], check=True)
        if sha(archive) != e['sha256']:
            raise RuntimeError('Source hash mismatch: ' + e['name'])
        target = out / e['name']
        target.mkdir()
        with tarfile.open(archive) as tar:
            for m in tar.getmembers():
                path = target / m.name
                if not path.resolve().is_relative_to(target):
                    raise RuntimeError('Unsafe source path')
                if m.issym() or m.islnk():
                    parent = path.parent if m.issym() else target
                    if not (parent / m.linkname).resolve().is_relative_to(target):
                        raise RuntimeError('Unsafe source link')
            tar.extractall(target)
        roots = [f for f in target.iterdir() if f.is_dir()]
        if len(roots) != 1:
            raise RuntimeError('Expected one source root')
        sources[e['name']] = roots[0]

    usb = sources['libusb']
    run('usb-bootstrap', ['./bootstrap.sh'], usb)
    run('usb-configure', ['./configure', '--prefix=' + str(prefix), '--disable-static'], usb,
        {'CFLAGS': '-O2 -g -mmacosx-version-min=14.0 -Wl,-headerpad_max_install_names'})
    run('usb-build', ['make', '-j1'], usb)
    run('usb-install-private-prefix', ['make', '-j1', 'install'], usb)
    jpeg_build = out / 'jpeg-build'
    run('jpeg-configure', ['cmake', '-S', str(sources['jpeg']), '-B', str(jpeg_build),
        '-DCMAKE_INSTALL_PREFIX=' + str(prefix), '-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_OSX_DEPLOYMENT_TARGET=14.0', '-DENABLE_SHARED=ON', '-DENABLE_STATIC=OFF',
        '-DWITH_SIMD=OFF', '-DWITH_TURBOJPEG=OFF',
        '-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-headerpad_max_install_names'], out)
    run('jpeg-build', ['cmake', '--build', str(jpeg_build), '--parallel', '1'], out)
    run('jpeg-install-private-prefix', ['cmake', '--install', str(jpeg_build)], out)
    sane = sources['sane']
    patches = sorted((here / 'patches').glob('*.patch'))
    names = ['sane-epsonds-es60w-length-experiment.patch', 'sane-epsonds-es60w-option.patch',
             'sane-epsonds-final-payload.patch', 'sane-epsonds-jpeg-bounded-diagnostic.patch',
             'sane-epsonds-height-rounding.patch']
    assert set(names) == {x.name for x in patches}
    for name in names:
        subprocess.run(['git', 'apply', '--check', str(here / 'patches' / name)], cwd=sane, check=True)
        subprocess.run(['git', 'apply', str(here / 'patches' / name)], cwd=sane, check=True)
    # The final binary is built from the annotated sources delivered in the kit.
    for name in ['backend/epsonds.c', 'backend/epsonds.h', 'backend/epsonds-jpeg.c',
                 'backend/epsonds-ops.c', 'backend/epsonds-cmd.c', 'backend/epsonds-jpeg.h']:
        f = sane / name
        f.write_text(f.read_text().rstrip() +
                     '\n\n/* Modified by Pengusto on 2026-10-25: ES-60W transport and length handling. */\n')
    flags = {'BACKENDS': 'epsonds', 'USB_CFLAGS': '-I' + str(prefix / 'include/libusb-1.0'),
             'USB_LIBS': '-L' + str(prefix / 'lib') + ' -lusb-1.0',
             'CPPFLAGS': '-I' + str(prefix / 'include'), 'LDFLAGS': '-L' + str(prefix / 'lib'),
             'CFLAGS': '-O1 -g -mmacosx-version-min=14.0 -Wl,-headerpad_max_install_names',
             'PKG_CONFIG_LIBDIR': str(prefix / 'lib/pkgconfig')}
    opts = ['--disable-nls', '--disable-static'] + ['--without-' + n for n in
        ['avahi', 'snmp', 'gphoto2', 'v4l', 'poppler-glib', 'libcurl',
         'usb-record-replay', 'systemd', 'tiff', 'png']]
    run('sane-configure', ['./configure', *opts], sane, flags)
    run('sane-build', ['make', '-j1'], sane, flags)
    stage = out / 'helper'
    files = {'MacOS/scanimage': sane / 'frontend/.libs/scanimage',
             'Frameworks/libsane.1.dylib': sane / 'backend/.libs/libsane.1.dylib',
             'Frameworks/sane/libsane-epsonds.1.so': sane / 'backend/.libs/libsane-epsonds.1.so',
             'Frameworks/libusb-1.0.0.dylib': prefix / 'lib/libusb-1.0.0.dylib',
             'Frameworks/libjpeg.62.dylib': prefix / 'lib/libjpeg.62.dylib'}
    for name, f in files.items():
        dest = stage / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
    names_to_paths = {p.name: stage / n for n, p in files.items()}
    for name in files:
        f = stage / name
        args = []
        for line in subprocess.check_output(['otool', '-L', str(f)], text=True).splitlines()[1:]:
            old = line.strip().split(' (', 1)[0]
            dest = names_to_paths.get(Path(old).name)
            if dest:
                args += ['-change', old, '@loader_path/' + os.path.relpath(dest, f.parent)]
            elif not old.startswith(('/System/Library/', '/usr/lib/')):
                raise RuntimeError('Non-system dependency missing from bundle: ' + old)
        if f.name != 'scanimage':
            args += ['-id', '@loader_path/' + f.name]
        if args:
            subprocess.run(['install_name_tool', *args, str(f)], check=True)
    shutil.copytree(here / 'config', stage / 'Resources/config')
    notices = stage / 'Resources/notices'
    for component, paths in {'sane': ['COPYING', 'LICENSE', 'AUTHORS'],
                             'libusb': ['COPYING', 'AUTHORS'],
                             'jpeg': ['LICENSE.md', 'README.ijg']}.items():
        for name in paths:
            f = sources[component] / name
            if f.exists():
                dest = notices / component / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
    report = {'native_dependency_sources_built': ['libusb-1.0.30', 'libjpeg-turbo-3.2.0'],
              'workers': 1, 'installed_systemwide': False, 'device_commands': 0,
              'source_archives': entries, 'patches_sha256': {n: sha(here / 'patches' / n) for n in names},
              'files_sha256': {n: sha(stage / n) for n in files},
              'other_bundled_native_libraries_rebuilt': False}
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Native helper source build complete', flush=True)


if __name__ == '__main__':
    main()
