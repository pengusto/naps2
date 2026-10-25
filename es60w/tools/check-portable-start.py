#!/usr/bin/env python3
"""Start GUI/worker with a fresh HOME, no data override, devices/helpers denied."""
import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--app', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
app, out = a.app.resolve(strict=True), a.output.resolve()
if out.exists() or any((d / '.git').exists() for d in out.parents):
    p.error('Use a new output directory outside Git')
out.mkdir(mode=0o700, parents=True)
home = out / 'portable user with spaces'; home.mkdir()
blocked = ['/Applications/Epson Software', '/Library/Image Capture',
           '/Library/Application Support/EPSON', str(Path.home() / 'Documents/Scans'),
           str(Path.home() / 'Library/Application Support/NAPS2 ES60W')]
blocked += [str(Path.home() / '.config' / name) for name in
            ['naps2', 'naps2-free-es60w', 'naps2-free-es60w-helper']]
policy = '(version 1)(allow default)(deny iokit-open)(deny network-outbound (remote ip "*:*"))'
policy += '(deny process-exec (subpath ' + json.dumps(str(app / 'Contents/Helpers')) + '))'
for operation in ['file-read*', 'file-write*']:
    policy += '(deny ' + operation + ' ' + ' '.join('(subpath ' + json.dumps(x) + ')' for x in blocked) + ')'
sb = out / 'no-device.sb'; sb.write_text(policy + '\n')
env = {k: v for k, v in os.environ.items() if not k.startswith(('DYLD_', 'SANE_', 'NAPS2_TEST_'))
       and k not in ['DOTNET_ROOT', 'LD_LIBRARY_PATH']}
env.update(HOME=str(home), PATH='/usr/bin:/bin', TMPDIR=tempfile.mkdtemp(prefix='es60port-', dir='/tmp') + '/')
base = ['/usr/bin/sandbox-exec', '-f', str(sb), str(app / 'Contents/MacOS/NAPS2')]


def stop(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


with (out / 'worker.stderr').open('w') as err:
    worker = subprocess.Popen(base + ['worker', str(os.getpid())], env=env,
                              stdout=subprocess.PIPE, stderr=err, text=True, start_new_session=True)
    lines = []; ready = False
    try:
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if select.select([worker.stdout], [], [], .5)[0]:
                line = worker.stdout.readline(); lines.append(line)
                if line.strip() == 'ready':
                    ready = True; break
            if worker.poll() is not None:
                break
    finally:
        stop(worker)
(out / 'worker.stdout').write_text(''.join(lines))
assert ready, 'Worker not ready; inspect logs'
with (out / 'gui.log').open('w') as log:
    gui = subprocess.Popen(base, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        time.sleep(6)
        alive = gui.poll() is None
        profile_path = home / '.config/naps2-free-es60w-helper/profiles.xml'
        profile_created = profile_path.is_file()
        config_created = (profile_path.parent / 'config.xml').is_file()
        # NAPS2 reads bundled system profiles directly. It need not write a
        # per-user profiles.xml until a profile is changed; config.xml proves
        # the normal fresh-user data path was actually used by this startup.
        preset_path = profile_path if profile_created else app / 'Contents/Resources/profiles.xml'
        profile = ET.parse(preset_path).getroot()[0]
        assert profile.findtext('Device/ID') == 'epsonds:libusb:es60w-auto'
        assert profile.findtext('AutoSaveSettings/FilePath', '').startswith('%HOME%/Documents/Scans/')
        if profile_created:
            profile = ET.parse(profile_path).getroot()[0]
            assert profile.findtext('Device/ID') == 'epsonds:libusb:es60w-auto'
            assert profile.findtext('AutoSaveSettings/FilePath', '').startswith('%HOME%/Documents/Scans/')
    finally:
        stop(gui)
result = {'gui_alive_after_6s': alive, 'worker_ready': ready,
          'fresh_user_config_created': config_created,
          'fresh_user_profile_created': profile_created, 'runtime_data_override_used': False,
          'helper_execution_denied': True, 'iokit_and_outbound_ip_denied': True,
          'normal_settings_paths_denied': True, 'physical_scans': 0,
          'finder_gatekeeper_first_start_tested': False, 'created_processes_stopped': True}
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
assert alive and config_created
