#!/usr/bin/env python3
"""Offline-only receiver/parser/lifecycle checks. Never invokes --listen on real receiver."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--app', required=True, type=Path)
p.add_argument('--dotnet', required=True, type=Path)
p.add_argument('--output', required=True, type=Path, help='NEW directory outside Git')
p.add_argument('--libusb-header', type=Path, help='Pinned API header for extra native USB simulation (no libusb linkage)')
a = p.parse_args()
app, out = a.app.resolve(strict=True), a.output.resolve()
if any((root / '.git').exists() for root in [out, *out.parents]):
    p.error('Test artifacts must stay outside Git')
out.mkdir(parents=True, exist_ok=False)
source = Path(__file__).resolve().parent / 'scanner-button'
if not source.is_dir(): source = Path(__file__).resolve().parent
native = app / 'Contents/Helpers/ScanHelper.bundle/Contents/MacOS/scanner-button'
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
policy = '(version 1)(allow default)(deny iokit-open)(deny network-outbound (remote ip "*:*"))'
policy += '(deny file-read* (subpath "/Library/Image Capture") (subpath "/Applications/Epson Software") (subpath "/Library/Application Support/EPSON"))'
policy += '(deny mach-lookup (global-name-regex #"com\\.epson\\..*"))'
sb = out / 'no-hardware.sb'; sb.write_text(policy + '\n')
prefix = ['/usr/bin/sandbox-exec', '-f', str(sb)]
selftest = subprocess.check_output(prefix + [str(native), '--self-test'], text=True)
(out / 'native-self-test.json').write_text(selftest)
assert json.loads(selftest) == dict(parser_cases=266, gate_cases=8, usb_initialized=False, scan_commands=0)
imports = subprocess.check_output(['nm', '-u', str(native)], text=True)
(out / 'native-imports.txt').write_text(imports)
usb_names = sorted({line.split()[-1] for line in imports.splitlines() if '_libusb_' in line})
allowed = {'claim_interface','close','error_name','exit','free_config_descriptor','free_device_list',
           'get_active_config_descriptor','get_bus_number','get_device_address','get_device_descriptor',
           'get_device_list','init','interrupt_transfer','open','release_interface'}
assert set(usb_names) == {'_libusb_' + s for s in allowed}, usb_names
links = subprocess.check_output(['otool', '-L', str(native)], text=True)
(out / 'native-libraries.txt').write_text(links)
assert '@loader_path/../Frameworks/libusb-1.0.0.dylib' in links
assert all(line.strip().startswith(('@loader_path/', '/usr/lib/', '/System/Library/')) for line in links.splitlines()[1:])
project = out / 'managed'; project.mkdir()
for name in ['Check.csproj', 'Check.cs', 'ScannerButtonSession.cs', 'ScannerButtonTransport.cs']:
    shutil.copy2(source / name, project / name)
fake = out / 'replay-button'
subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1',
                '-mmacosx-version-min=14.0', str(source/'ReplayButton.c'), '-o', str(fake)], check=True)
env = dict(os.environ, DOTNET_PROCESSOR_COUNT='1', DOTNET_CLI_USE_MSBUILD_SERVER='0', MSBUILDDISABLENODEREUSE='1')
with (out/'managed-build.log').open('w') as log:
    subprocess.run([str(a.dotnet.resolve()), 'build', str(project/'Check.csproj'), '--disable-build-servers',
        '-maxcpucount:1', '-p:BuildInParallel=false', '-p:UseSharedCompilation=false'],
        env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
(out/'process-controls').mkdir()
controls = subprocess.check_output(prefix + [str(a.dotnet.resolve()),
    str(project/'bin/Debug/net10.0/Check.dll'), str(fake), str(out/'process-controls')], env=env, text=True)
(out/'managed-controls.json').write_text(controls)
assert json.loads(controls) == dict(controls_passed=36, hardware_scans=0, device_commands=0)
report = dict(native_parser_cases=266, native_gate_cases=8, managed_controls=36, native_dependencies_bundled_or_system=True,
    native_usb_imports=usb_names, hardware_scans=0, actual_receiver_listen_invocations=0,
    iokit_epson_and_outbound_ip_denied=True, physical_button_verified=False)
if a.libusb_header:
    header = a.libusb_header.resolve(strict=True)
    assert hashlib.sha256(header.read_bytes()).hexdigest() == 'a61260ab145b051b86df2b0575956f01810190abe2c7df6aca831c33bdc8082c'
    simulated = out / 'offline-native-receiver'
    subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1',
        '-mmacosx-version-min=14.0', '-I', str(header.parent), str(source/'ScannerButton.c'),
        str(source/'ReplayUsb.c'), '-o', str(simulated)], check=True)
    # Statically compiled fake API: there must be no real USB imports or dylib.
    assert '_libusb_' not in subprocess.check_output(['nm', '-u', str(simulated)], text=True)
    assert 'libusb' not in subprocess.check_output(['otool', '-L', str(simulated)], text=True)
    cases = {'missing': (75, ['retry\tmissing']),
        'config-gone': (75, ['retry\tdisconnected']), 'open-gone': (75, ['retry\tdisconnected']),
        'claim-gone': (75, ['retry\tdisconnected']), 'busy': (75, ['retry\tbusy']),
        'read-gone': (75, ['ready\tepsonds:libusb:001:009', 'retry\tdisconnected']),
        'io-gone': (75, ['ready\tepsonds:libusb:001:009', 'retry\tdisconnected']),
        'io-replaced': (75, ['ready\tepsonds:libusb:001:009', 'retry\tdisconnected']),
        'io-enumeration-error': (1, ['ready\tepsonds:libusb:001:009']),
        'io-present': (1, ['ready\tepsonds:libusb:001:009']),
        'noise-press': (0, ['ready\tepsonds:libusb:001:009', 'button\t0\tepsonds:libusb:001:009']),
        'badread': (1, []), 'ambiguous': (1, [])}
    replay = []
    for name, (code, lines) in cases.items():
        test = subprocess.run(prefix+[str(simulated), '--listen', str(out/('native-'+name+'.lock'))],
            env=dict(env, NAPS2_BUTTON_REPLAY_CASE=name), text=True, capture_output=True, timeout=5)
        assert test.returncode == code and test.stdout.splitlines() == lines, (name, test)
        reads = {'noise-press': 7, 'read-gone': 3, 'badread': 1,
                 'io-gone': 3, 'io-replaced': 3, 'io-enumeration-error': 3, 'io-present': 3}.get(name, 0)
        assert f'replay-cleanup opened=0 claimed=0 reads={reads}' in test.stderr, (name, test.stderr)
        (out/('native-'+name+'.stderr')).write_text(test.stderr)
        replay.append(dict(case=name, exit_code=code, lines=lines, simulated_interrupt_reads=reads, usb_handles_released=True))
    (out/'native-usb-simulation.json').write_text(json.dumps(replay, indent=2)+'\n')
    report['native_usb_simulation_cases'] = len(replay)
    report['simulated_native_has_real_usb_linkage'] = False
(out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
