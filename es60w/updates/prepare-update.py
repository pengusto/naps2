#!/usr/bin/env python3
"""Prepare a signed, complete-app update locally. Never uploads or installs."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app', type=Path, required=True)
    p.add_argument('--sparkle-tools', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--download-url-prefix', required=True)
    p.add_argument('--account', default='de.pengusto.naps2.es60w.updates')
    p.add_argument('--local-test', action='store_true')
    p.add_argument('--test-key-file', type=Path, help='Disposable key outside Git, local tests only')
    a = p.parse_args()
    app, out, tools = a.app.resolve(strict=True), a.output.resolve(), a.sparkle_tools.resolve(strict=True)
    if out.exists() or any((d / '.git').exists() for d in [out] + list(out.parents)):
        p.error('Use a new output directory outside Git')
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    url = urlsplit(a.download_url_prefix)
    if a.local_test:
        if url.scheme != 'http' or url.hostname != '127.0.0.1' or not url.port:
            p.error('Local tests require an explicit loopback URL')
        if not info['CFBundleIdentifier'].startswith('de.pengusto.naps2.es60w.updatetest.'):
            p.error('Local test updates must use a disposable test bundle identifier')
    elif not (url.scheme == 'https' and url.hostname == 'github.com'
              and url.path.startswith('/pengusto/naps2/releases/download/')
              and not info.get('ES60WLocalUpdateTest')
              and info['CFBundleIdentifier'] == 'de.pengusto.naps2.es60w'):
        p.error('Only the own fork and non-test application are release inputs')
    if not (info.get('SURequireSignedFeed') and info.get('SUVerifyUpdateBeforeExtraction')):
        p.error('Signed feeds and archive verification before extraction are required')
    if a.test_key_file:
        key = a.test_key_file.resolve(strict=True)
        if not a.local_test or key.stat().st_mode & 0o077 or any((d / '.git').exists() for d in key.parents):
            p.error('Test keys must be private files outside Git and require --local-test')
        pub = Path(str(key) + '.pub').read_text().strip()
        signing = ['--ed-key-file', str(key)]
    else:
        pub = subprocess.check_output([str(tools / 'generate_keys'), '--account', a.account, '-p'], text=True).strip()
        signing = ['--account', a.account]
    if pub != info.get('SUPublicEDKey'):
        p.error('Signing account does not match the application public key')
    helper = app / 'Contents/Helpers/ScanHelper.bundle/Contents'
    for name in ['MacOS/scanimage-real', 'Frameworks/libsane.1.dylib',
                 'Frameworks/sane/libsane-epsonds.1.so', 'Resources/staging-input-manifest.json']:
        if not (helper / name).is_file():
            p.error('Incomplete app/helper update: ' + name)
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
    out.mkdir(parents=True)
    archive = out / ('NAPS2-ES60W-' + info['CFBundleVersion'] + '-arm64.zip')
    subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(app), str(archive)], check=True)
    command = [str(tools / 'generate_appcast')] + signing + ['--maximum-deltas', '0',
        '--download-url-prefix', a.download_url_prefix.rstrip('/') + '/',
        '--link', 'https://github.com/pengusto/naps2', str(out)]
    subprocess.run(command, check=True)
    appcasts = list(out.glob('*.xml'))
    if len(appcasts) != 1:
        raise RuntimeError('Expected exactly one signed appcast')
    feed = appcasts[0]
    if feed.name != 'appcast.xml':
        feed.rename(out / 'appcast.xml'); feed = out / 'appcast.xml'
    subprocess.run([str(tools / 'sign_update')] + signing + ['--verify', str(feed)], check=True)
    enclosure = ET.parse(feed).find('./channel/item/enclosure')
    signature = enclosure.get('{http://www.andymatuschak.org/xml-namespaces/sparkle}edSignature')
    if not signature:
        raise RuntimeError('Update archive signature missing')
    subprocess.run([str(tools / 'sign_update')] + signing + ['--verify',
        str(archive), signature], check=True)
    evidence = {'bundle_id': info['CFBundleIdentifier'], 'version': info['CFBundleVersion'],
        'complete_app_including_sane': True, 'helper_manifest_sha256': hashlib.sha256(
            (helper / 'Resources/staging-input-manifest.json').read_bytes()).hexdigest(),
        'ed25519_archive_verified': True, 'ed25519_feed_verified': True,
        'uploaded': False, 'installed': False, 'local_test': a.local_test,
        'files_sha256': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in [archive, feed]}}
    (out / 'update.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (out / 'SHA256SUMS').write_text(''.join(h + '  ' + n + '\n' for n, h in evidence['files_sha256'].items()))
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
