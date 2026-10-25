#!/usr/bin/env python3
"""Exercise the actual AutoSaver in a disposable native replay copy. No USB.

The installed app and its settings remain untouched. The copied native receiver
is replaced by an explicitly marked file fixture; IOKit, real backends, Epson,
network and installed settings are denied. Test PDFs stay outside Documents.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from PIL import Image
from pypdf import PdfReader

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--app', type=Path, required=True)
p.add_argument('--original', type=Path, required=True)
p.add_argument('--expected', type=Path, required=True)
p.add_argument('--entitlements', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--portable-home', action='store_true', help='Keep and test the packaged %%HOME%% path')
a = p.parse_args()
app, out = a.app.resolve(), a.output.resolve()
scripts = Path(__file__).resolve().parent
repo = scripts.parent.parent
assert repo != out and repo not in out.parents, 'Keep images outside Git'
out.mkdir(parents=True, exist_ok=False, mode=0o700)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest(path):
    return {str(f.relative_to(path)): sha(f) for f in path.rglob('*')
            if f.is_file() and not f.is_symlink()}

before = manifest(app)
original_hash = sha(a.original)
installed_info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
installed_data = Path(installed_info.get('LSEnvironment', {}).get(
    'NAPS2_TEST_DATA', str(Path.home() / '.config/naps2-free-es60w-helper')))
data_before = {str(f): sha(f) for f in installed_data.glob('*.xml')}
fixture = out / 'input.tiff'
with Image.open(a.original) as im:
    im.convert('RGB').save(fixture, compression='raw', dpi=(300, 300))
replay = out / 'Offline AutoSave Check.app'
subprocess.run(['ditto', str(app), str(replay)], check=True)
native = replay / 'Contents/Helpers/ScanHelper.bundle/Contents/MacOS/scanimage-real'
subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1',
                '-mmacosx-version-min=14.0', str(scripts / 'helper-client/ReplayScanImage.c'),
                '-o', str(native)], check=True)
info_path = replay / 'Contents/Info.plist'
info = plistlib.loads(info_path.read_bytes())
info.update(CFBundleIdentifier='de.pengusto.naps2.es60w.offline-autosave-check',
            CFBundleName='Offline AutoSave Check')
info.pop('LSEnvironment', None)
info_path.write_bytes(plistlib.dumps(info))
(replay / 'Contents/Resources/offline-replay-only.marker').write_text('FILE FIXTURE; NEVER INSTALL\n')
for target in [native, replay / 'Contents/Helpers/ScanHelper.bundle']:
    subprocess.run(['codesign', '--force', '--sign', '-', '--options', '0', str(target)],
                   check=True, capture_output=True)
subprocess.run(['codesign', '--force', '--sign', '-', '--options', '0',
                '--entitlements', str(a.entitlements.resolve()), str(replay)],
               check=True, capture_output=True)
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(replay)], check=True)
data = out / 'data'; data.mkdir(mode=0o700)
portable_home = out / 'different user home with spaces'
pdfs = portable_home / 'Documents/Scans' if a.portable_home else out / 'pdfs'
if a.portable_home:
    portable_home.mkdir()
else:
    pdfs.mkdir(parents=True)
profile = ET.parse(app / 'Contents/Resources/profiles.xml')
s = profile.getroot()[0]
assert s.findtext('EnableAutoSave') == 'true'
assert s.findtext('AutoSaveSettings/PromptForFilePath') == 'false'
assert s.findtext('AutoSaveSettings/Separator') == 'FilePerScan'
original_template = Path(s.findtext('AutoSaveSettings/FilePath'))
if a.portable_home:
    assert str(original_template).startswith('%HOME%/Documents/Scans/')
else:
    s.find('AutoSaveSettings/FilePath').text = str(pdfs / original_template.name)
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
profile.write(data / 'profiles.xml', encoding='utf-8', xml_declaration=True)
denied = [str(installed_data), str(Path.home() / 'Documents/Scans'),
          '/Applications/Epson Software', '/Library/Image Capture',
          '/Library/Application Support/EPSON', '/Library/Printers/EPSON',
          '/Library/Printers/Epson', '/usr/local/lib',
          str(replay / 'Contents/Helpers/ScanHelper.bundle/Contents/Frameworks/sane')]
denied += [str(Path.home() / '.config' / x) for x in
           ['naps2', 'naps2-free-es60w', 'naps2-free-es60w-helper']]
policy = '(version 1)(allow default)(deny iokit-open)(deny network-outbound (remote ip "*:*"))'
for operation in ['file-read*', 'file-write*']:
    policy += '(deny ' + operation + ' ' + ' '.join(
        '(subpath ' + json.dumps(x) + ')' for x in denied) + ')'
sb = out / 'no-hardware.sb'; sb.write_text(policy + '\n')
env = {k: v for k, v in os.environ.items() if not k.startswith(('DYLD_', 'SANE_', 'NAPS2_TEST_'))
       and k not in ['DOTNET_ROOT', 'LD_LIBRARY_PATH']}
env.update(NAPS2_TEST_DATA=str(data), NAPS2_TEST_REPLAY_TIFF=str(fixture),
           NAPS2_TEST_REPLAY_DEVICE_NAME='Epson ES-60W', PATH='/usr/bin:/bin',
           NAPS2_TEST_REPLAY_DEVICE_ID=s.findtext('Device/ID'),
           TMPDIR=tempfile.mkdtemp(prefix='es60auto-', dir='/tmp') + '/')
if a.portable_home:
    env.update(HOME=str(portable_home))
cmd = ['/usr/bin/sandbox-exec', '-f', str(sb), str(replay / 'Contents/MacOS/NAPS2'),
       'cli', '-p', s.findtext('DisplayName'), '--driver', 'sane', '--device', 'ES-60W',
       '-n', '1', '--autosave', '--disableocr', '--progress', '--verbose']
with (out / 'stdout.log').open('w') as stdout, (out / 'stderr.log').open('w') as stderr:
    proc = subprocess.Popen(cmd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
    try:
        code = proc.wait(timeout=45)
    finally:
        try: os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError: pass
assert code == 0, 'Inspect offline test logs'
generated = list(pdfs.glob('*.pdf'))
assert len(generated) == 1, 'Expected one automatically named PDF without a save dialog'
reader = PdfReader(generated[0]); assert len(reader.pages) == 1
box = reader.pages[0].mediabox
mm = [float(box.width) / 72 * 25.4, float(box.height) / 72 * 25.4]
with Image.open(a.expected) as im: expected_mm = [n / 300 * 25.4 for n in im.size]
assert all(abs(x - y) < .02 for x, y in zip(mm, expected_mm))
assert manifest(app) == before and sha(a.original) == original_hash
assert all(sha(Path(f)) == h for f, h in data_before.items())
result = dict(physical_scans=0, hardware_and_outbound_ip_denied=True,
    native_file_fixture_only=True, actual_app_autosaver_exercised=True,
    automatically_named_pdf=True, generated_pdfs=1, pdf_pages=1, pdf_mm=mm,
    save_prompt=False, installed_app_and_settings_unchanged=True,
    original_unchanged=True, documents_folder_denied=True,
    replay_app_removed=True)
result['portable_home_placeholder_tested'] = a.portable_home
result['portable_output_directory_created'] = a.portable_home and pdfs.is_dir()
shutil.rmtree(replay)
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
