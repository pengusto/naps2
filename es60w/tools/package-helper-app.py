#!/usr/bin/env python3
"""Package a FULL external-helper app build at a NEW path; preserve installed apps."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-app', type=Path, required=True)
    p.add_argument('--overlay', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--entitlements', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True, help='NEW JSON report outside the app')
    p.add_argument("--scanner-button-header", type=Path, help="Pinned libusb.h for own receiver")
    a = p.parse_args()
    source, dest = a.source_app.resolve(), a.destination.resolve()
    if dest.exists() or dest.suffix != '.app' or a.report.exists():
        p.error('Destination app and report must be new')
    lib = source / 'Contents/MonoBundle/NAPS2.Lib.dll'
    sdk = source / 'Contents/MonoBundle/NAPS2.Sdk.dll'
    for path, literal in [(lib, 'naps2-free-es60w-helper'), (sdk, 'external-scanimage.marker')]:
        if literal.encode('utf-16le') not in path.read_bytes():
            p.error('Missing compiled helper integration: ' + literal)
    dest.parent.mkdir(parents=True, exist_ok=True)
    removed = []
    with tempfile.TemporaryDirectory(prefix='naps2-helper-package-', dir=dest.parent) as tmp:
        stage = Path(tmp) / 'NAPS2.app'
        subprocess.run(['ditto', str(source), str(stage)], check=True)
        resources = stage / 'Contents/Resources'
        subprocess.run(['ditto', str(a.overlay.resolve() / 'Contents'), str(stage / 'Contents')], check=True)
        helper = stage / 'Contents/Helpers/ScanHelper.bundle'
        if not (helper / 'Contents/MacOS/scanimage').is_file() or any(helper.rglob('test-support')):
            raise RuntimeError('Requires production helper overlay without test backend')
        # The native launcher is inert unless an owned diagnostic directory is
        # explicitly supplied. It also provides a consistent offline replay seam.
        launcher_source = Path(__file__).resolve().parent / 'helper-client/BundledScanImageLauncher.c'
        (helper / 'Contents/MacOS/scanimage').rename(helper / 'Contents/MacOS/scanimage-real')
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1',
                        '-mmacosx-version-min=14.0', str(launcher_source),
                        '-o', str(helper / 'Contents/MacOS/scanimage')], check=True)
        if a.scanner_button_header:
            header = a.scanner_button_header.resolve(strict=True)
            if hashlib.sha256(header.read_bytes()).hexdigest() != "a61260ab145b051b86df2b0575956f01810190abe2c7df6aca831c33bdc8082c":
                raise RuntimeError("Unexpected libusb API header")
            if "scanner-button.marker".encode("utf-16le") not in lib.read_bytes():
                raise RuntimeError("Missing compiled button integration")
            button = helper / "Contents/MacOS/scanner-button"
            button_source = Path(__file__).resolve().parent / "scanner-button/ScannerButton.c"
            usb = helper / "Contents/Frameworks/libusb-1.0.0.dylib"
            subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O1",
                            "-Wl,-headerpad_max_install_names", "-mmacosx-version-min=14.0",
                            "-I", str(header.parent), str(button_source), str(usb), "-o", str(button)], check=True)
            subprocess.run(["install_name_tool", "-change", "@loader_path/libusb-1.0.0.dylib",
                            "@loader_path/../Frameworks/libusb-1.0.0.dylib", str(button)], check=True)
            (resources / "scanner-button.marker").write_text("USB interrupt receiver; UI opt-in each session; no scan at startup.\n")
            notices = helper / "Contents/Resources/notices/scanner-button"
            notices.mkdir()
            shutil.copy2(Path(__file__).resolve().parent.parent / "LICENSE-tools.txt", notices / "LICENSE")
        # These are the unused direct SANE backend collection/loader and its private deps.
        # Shared image/OCR/PDF libraries stay; none loads these removed names (checked below).
        for root in (resources, stage / 'Contents/MonoBundle'):
            for native in root.glob('_mac*'):
                for path in [native / 'sane', native / 'libsane.1.dylib',
                             native / 'libusb-1.0.0.dylib', native / 'libjpeg.62.dylib']:
                    if path.exists() or path.is_symlink():
                        removed.append(str(path.relative_to(stage)))
                        if path.is_dir(): shutil.rmtree(path)
                        else: path.unlink()
            config = root / '_config/sane'
            if config.is_dir():
                removed.append(str(config.relative_to(stage)))
                shutil.rmtree(config)
        forbidden = ('libsane', 'libusb-1.0', 'libjpeg.62')
        magic = (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca')
        for path in stage.rglob('*'):
            if not path.is_file() or path.is_symlink() or helper in path.parents: continue
            with path.open('rb') as f: head = f.read(4)
            if head not in magic: continue
            deps = subprocess.check_output(['otool', '-L', str(path)], text=True).splitlines()[1:]
            if any(any(name in line for name in forbidden) for line in deps):
                raise RuntimeError('Remaining app library needs removed direct SANE dependency: ' + str(path))
        (resources / 'free-es60w.marker').write_text('experimental-external-helper-v1\n')
        scripts = Path(__file__).resolve().parent
        shutil.copy2(scripts / 'defaults/profiles.xml', resources / 'profiles.xml')
        shutil.copy2(scripts / 'defaults/appsettings.xml', resources / 'appsettings.xml')
        shutil.copytree(scripts.parent / 'licenses', resources / 'LicenseReview', dirs_exist_ok=True)
        config = ET.parse(resources / 'appsettings.xml')
        for name, value in {'AlwaysRememberDevice': 'true', 'NoUpdatePrompt': 'true',
                            'OcrDefaultAfterScanning': 'false'}.items():
            element = config.getroot().find(name)
            if element is None: raise RuntimeError('Missing setting: ' + name)
            element.text = value
            element.set('mode', 'default')
        config.write(resources / 'appsettings.xml', encoding='utf-8', xml_declaration=True)
        info = stage / 'Contents/Info.plist'
        data = plistlib.loads(info.read_bytes())
        data.update(CFBundleIdentifier='de.pengusto.naps2.es60w',
                    CFBundleName='NAPS2 ES60W', CFBundleDisplayName='NAPS2 ES60W',
                    CFBundleVersion='851002', CFBundleShortVersionString='8.5.1')
        data.pop('LSEnvironment', None)
        data.pop('CFBundleDocumentTypes', None)
        data.pop('CFBundleURLTypes', None)
        info.write_bytes(plistlib.dumps(data))
        # Debug paths are not runtime inputs; keep exported symbols, remove DWARF.
        for path in stage.rglob('*'):
            if path.is_symlink() or not path.is_file():
                continue
            with path.open('rb') as stream:
                head = stream.read(4)
            if head in magic:
                commands = subprocess.check_output(['otool', '-l', str(path)], text=True)
                rpaths = re.findall(r'cmd LC_RPATH\n.*?\n\s*path (.+?) \(offset', commands)
                for rpath in rpaths:
                    if rpath.startswith('/') and not rpath.startswith(('/usr/lib/', '/System/Library/')):
                        subprocess.run(['install_name_tool', '-delete_rpath', rpath, str(path)], check=True)
                subprocess.run(['strip', '-S', str(path)], check=True)
        shutil.copy2(scripts.parent / 'SOURCE-STATUS.json', resources / 'LicenseReview/SOURCE-STATUS.json')
        manifest = helper / 'Contents/Resources/staging-input-manifest.json'
        provenance = json.loads(manifest.read_text())
        for path in stage.rglob('*'):
            if path.is_file() and not path.is_symlink() and str(Path.home()).encode() in path.read_bytes():
                raise RuntimeError('Personal build path remains in package: ' + str(path.relative_to(stage)))
        provenance['manifest_scope'] = 'Standalone staging inputs before final whole-app signing'
        manifest.write_text(json.dumps(provenance, indent=2) + '\n')
        subprocess.run([sys.executable, str(scripts / 'sign-test-copy.py'), str(stage), str(dest),
                        str(a.entitlements.resolve())], check=True)
    files = {}
    for path in sorted(dest.rglob('*')):
        if path.is_file():
            files[str(path.relative_to(dest))] = hashlib.sha256(path.read_bytes()).hexdigest()
    a.report.write_text(json.dumps({'bundle_id': data['CFBundleIdentifier'],
        'full_build_required_and_present': True, 'direct_sane_paths_removed': removed,
        'test_backend_in_app': False, 'files_sha256': files,
        'installed_apps_modified': False, 'hardware_scan': False, 'release_cleared': False,
        'scanner_button_integrated': a.scanner_button_header is not None,
        'scanner_button_physical_test': False, 'scanner_button_startup_armed': False}, indent=2) + '\n')
    print(dest)


if __name__ == '__main__':
    main()
