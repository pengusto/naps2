#!/usr/bin/env python3
"""Exercise real Sparkle with disposable complete apps and a loopback-only feed.

No scanner command, installed-app write, public upload or Paperless access.
The automated user driver is a separate test executable, not shipped in the app.
"""
import argparse
from functools import partial
import hashlib
import http.server
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import threading
import time
import uuid
import xml.etree.ElementTree as ET


def hashes(app):
    return {str(p.relative_to(app)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(app.rglob('*')) if p.is_file()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app', type=Path, required=True)
    p.add_argument('--sparkle', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    app, sparkle, out = a.app.resolve(strict=True), a.sparkle.resolve(strict=True), a.output.resolve()
    if out.exists() or any((d / '.git').exists() for d in [out] + list(out.parents)):
        p.error('Use a new output directory outside Git')
    if Path('/private/tmp') not in out.parents:
        p.error('Use /private/tmp for installer fixtures, avoiding protected Documents/Desktop folders')
    if (app / 'Contents/MacOS/UpdateProbe').exists():
        p.error('The real input app must not contain the automated test user driver')
    out.mkdir(parents=True, mode=0o700)
    here = Path(__file__).resolve().parent
    probe = out / 'UpdateProbe'
    subprocess.run(['clang', '-fobjc-arc', '-Wall', '-Wextra', '-Werror', '-arch', 'arm64',
        '-mmacosx-version-min=14.0', '-framework', 'Cocoa', '-framework', 'Sparkle',
        '-F' + str(sparkle), '-Wl,-rpath,@executable_path/../Frameworks',
        str(here / 'UpdateProbe.m'), '-o', str(probe)], check=True)
    key = out / 'disposable-test-key'
    subprocess.run(['xcrun', 'swift', str(here / 'MakeTestKey.swift'), str(key)], check=True)
    pub = Path(str(key) + '.pub').read_text().strip()
    served = out / 'server'; served.mkdir()
    requests = []

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            requests.append(self.path)

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(served)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    origin = 'http://127.0.0.1:' + str(server.server_port)
    bundle_id = 'de.pengusto.naps2.es60w.updatetest.' + uuid.uuid4().hex

    def fixture(dest, version, feed, is_old):
        subprocess.run(['ditto', str(app), str(dest)], check=True)
        file = dest / 'Contents/Info.plist'; info = plistlib.loads(file.read_bytes())
        info.update(CFBundleIdentifier=bundle_id, CFBundleName='ES60W Update Test',
            CFBundleDisplayName='ES60W Update Test', CFBundleVersion=str(version),
            SUPublicEDKey=pub, SUFeedURL=feed, SUEnableAutomaticChecks=False,
            ES60WLocalUpdateTest=True, NSAppTransportSecurity={'NSAllowsLocalNetworking': True})
        # Both fixtures launch only this harmless native probe, including the
        # newly installed app. A relaunch without test args exits immediately.
        shutil.copy2(probe, dest / 'Contents/MacOS/UpdateProbe')
        info['CFBundleExecutable'] = 'UpdateProbe'
        subprocess.run(['codesign', '--force', '--sign', '-', str(dest / 'Contents/MacOS/UpdateProbe')], check=True, capture_output=True)
        file.write_bytes(plistlib.dumps(info))
        # The original main executable is now nested code. Remove its old
        # Info.plist association, retaining the JIT entitlements for worker checks.
        subprocess.run(['codesign', '--force', '--sign', '-', '--preserve-metadata=entitlements',
            str(dest / 'Contents/MacOS/NAPS2')], check=True, capture_output=True)
        helper = dest / 'Contents/Helpers/ScanHelper.bundle'
        (helper / 'Contents/Resources/update-fixture-version').write_text(str(version) + '\n')
        subprocess.run(['codesign', '--force', '--sign', '-', str(helper)], check=True, capture_output=True)
        subprocess.run(['python3', str(here / 'sign-sparkle.py'), '--app', str(dest)], check=True)
        subprocess.run(['codesign', '--force', '--sign', '-', str(dest)], check=True, capture_output=True)
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(dest)], check=True)

    payload = out / 'payload/NAPS2 ES60W.app'
    fixture(payload, 851005, origin + '/good/appcast.xml', False)
    with (out / 'prepare.log').open('w') as log:
        subprocess.run(['python3', str(here / 'prepare-update.py'), '--app', str(payload),
            '--sparkle-tools', str(sparkle / 'bin'), '--output', str(served / 'good'),
            '--download-url-prefix', origin + '/good/', '--test-key-file', str(key), '--local-test'],
            check=True, stdout=log, stderr=subprocess.STDOUT)
    payload_hashes = hashes(payload)
    good = served / 'good'; archive = next(good.glob('*.zip')); base_feed = (good / 'appcast.xml').read_text()
    cases = ['good', 'postpone', 'bad-archive', 'bad-feed', 'old-version', 'cancel', 'cancel-ready', 'busy', 'missing-archive']
    for case in cases:
        if case == 'good': continue
        folder = served / case; folder.mkdir()
        shutil.copy2(archive, folder / archive.name)
        feed = base_feed.replace('/good/', '/' + case + '/')
        if case == 'old-version':
            feed = feed.replace('<sparkle:version>851005</sparkle:version>', '<sparkle:version>851000</sparkle:version>')
        (folder / 'appcast.xml').write_text(feed)
        subprocess.run([str(sparkle / 'bin/sign_update'), '--ed-key-file', str(key), str(folder / 'appcast.xml')], check=True, capture_output=True)
        if case == 'bad-feed':
            file = folder / 'appcast.xml'; file.write_text(file.read_text().replace('851005', '851006'))
        if case == 'bad-archive':
            file = folder / archive.name
            with file.open('r+b') as stream:
                stream.seek(-1, 2); value = stream.read(1); stream.seek(-1, 2); stream.write(bytes([value[0] ^ 1]))
        if case == 'missing-archive': (folder / archive.name).unlink()

    # Reject/cancel probes deny real hardware, installed apps/settings and all
    # outbound IP except the loopback feed. Full install probes run without this
    # wrapper: macOS refuses launchd installer registration from sandbox-exec.
    # They execute ONLY UpdateProbe, which contains no scanner interface; the
    # updated fixture also uses UpdateProbe as main; a relaunch immediately exits.
    blocked = ['/Applications', str(Path.home() / 'Applications'), '/Library/Image Capture',
        '/Library/Application Support/EPSON', str(Path.home() / 'Documents/Scans'),
        str(Path.home() / 'Library/Application Support/NAPS2 ES60W')]
    blocked += [str(Path.home() / '.config' / x) for x in ['naps2', 'naps2-free-es60w', 'naps2-free-es60w-helper']]
    sb = out / 'offline.sb'
    policy = '(version 1)(allow default)(deny iokit-open)(deny network-outbound (remote ip "*:*"))'
    policy += '(allow network-outbound (remote ip "localhost:' + str(server.server_port) + '"))'
    policy += '(deny file-read* ' + ' '.join('(subpath ' + json.dumps(x) + ')' for x in blocked) + ')'
    policy += '(deny file-write* ' + ' '.join('(subpath ' + json.dumps(x) + ')' for x in blocked) + ')'
    policy += '(deny process-exec (regex #".*/ScanHelper[.]bundle/Contents/MacOS/.*"))'
    sb.write_text(policy)
    subprocess.run(['sandbox-exec', '-f', str(sb), '/usr/bin/true'], check=True)
    results = []
    try:
        for case in cases:
            root = out / case; root.mkdir()
            target = root / 'NAPS2 ES60W.app'
            fixture(target, 851004, origin + '/' + case + '/appcast.xml', True)
            before = hashes(target)
            home = root / 'home'; home.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.startswith(('DYLD_', 'SANE_', 'NAPS2_TEST_'))}
            env.update(HOME=str(home), CFFIXED_USER_HOME=str(home), PATH='/usr/bin:/bin',
                NAPS2_TEST_DATA=str(home / 'naps2-data'), TMPDIR=str(root) + '/')
            result_file = root / 'events.plist'
            start = time.monotonic()
            install_case = case in ['good', 'postpone', 'bad-archive', 'cancel-ready']
            command = [str(target / 'Contents/MacOS/UpdateProbe'), str(result_file), case]
            if install_case:
                # Register the temporary application with LaunchServices so
                # Sparkle receives the real app-termination notification.
                command = ['open', '-n', '-W', '-j', '-a', str(target),
                    '--stdout', str(root / 'app.stdout'), '--stderr', str(root / 'app.stderr')]
                for name in ['HOME', 'CFFIXED_USER_HOME', 'NAPS2_TEST_DATA', 'TMPDIR']:
                    command += ['--env', name + '=' + env[name]]
                command += ['--args', str(result_file), case]
            else: command = ['sandbox-exec', '-f', str(sb)] + command
            with (root / 'process.log').open('w') as log:
                process = subprocess.Popen(command,
                    env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try: process.wait(timeout=55)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM); process.wait(timeout=5)
                    raise RuntimeError('Update probe did not finish: ' + case)
            if process.returncode:
                raise RuntimeError('Update probe failed before completion: ' + case + '; see process.log')
            if case in ['good', 'postpone']:
                deadline = time.monotonic() + 25
                while time.monotonic() < deadline:
                    info = plistlib.loads((target / 'Contents/Info.plist').read_bytes())
                    if info['CFBundleVersion'] == '851005': break
                    time.sleep(.25)
            events = plistlib.loads(result_file.read_bytes()) if result_file.exists() else []
            after = hashes(target)
            if case in ['good', 'postpone']:
                assert after == payload_hashes, 'Whole-app replacement incomplete: ' + case
                assert (target / 'Contents/Helpers/ScanHelper.bundle/Contents/Resources/update-fixture-version').read_text().strip() == '851005'
                if case == 'postpone': assert 'postponed' in events and 'idle-again' in events
            else:
                assert before == after, 'Rejected/cancelled update changed the app: ' + case
                expected = {'old-version': 'no-update', 'cancel': 'cancelled', 'cancel-ready': 'cancelled-ready',
                    'busy': 'busy-rejected'}.get(case, 'failed-safely')
                assert expected in events, 'Wrong result for ' + case + ': ' + str(events)
                if case == 'busy':
                    assert 'checking' not in events and not any(r.startswith('/busy/') for r in requests)
                if case in ['bad-archive', 'bad-feed']:
                    assert any('signature' in e.lower() for e in events), 'Signature failure was not demonstrated'
                    assert any('Code=3002' in e for e in events), 'Actual signature-validation error was not demonstrated'
            assert 'timeout' not in events and 'start-failed' not in events
            item = {'case': case, 'passed': True, 'elapsed_seconds': round(time.monotonic() - start, 2),
                'app_changed': before != after, 'probe_sandboxed': not install_case, 'events': events}
            results.append(item); print(json.dumps(item), flush=True)
            (out / 'result.json').write_text(json.dumps({'tests': results, 'completed': False}, indent=2) + '\n')
    finally:
        server.shutdown(); server.server_close()
        # Stop only temporary Sparkle helpers whose executable is inside this
        # run's private output. Never target a normal scanner application.
        listing = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True)
        for row in listing.splitlines():
            fields = row.strip().split(None, 1)
            if len(fields) == 2 and fields[1].startswith(str(out) + '/'):
                try: os.kill(int(fields[0]), signal.SIGTERM)
                except ProcessLookupError: pass
    result = {'tests': results, 'completed': True, 'feed_on_loopback_only': True, 'physical_scans': 0,
        'negative_probes_hardware_and_outbound_ip_denied': True,
        'full_install_probes_sandboxed': False, 'full_install_probes_execute_no_naps2_or_scanhelper': True,
        'test_user_driver_in_shipped_app': False, 'requests': requests}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
