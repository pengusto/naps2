#!/usr/bin/env python3
"""Embed a hash-pinned Sparkle runtime in an uninstalled staging bundle."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
from urllib.parse import urlsplit


def validate_config(data):
    if type(data.get('schema')) is not int or data['schema'] != 1:
        raise ValueError('Unsupported channel schema')
    for flag in ['automatic_checks', 'local_testing', 'published']:
        if type(data.get(flag)) is not bool:
            raise ValueError('Expected Boolean channel flag: ' + flag)
    key = base64.b64decode(data['public_ed_key'], validate=True)
    if len(key) != 32:
        raise ValueError('An Ed25519 public key must contain 32 bytes')
    url = urlsplit(data['feed_url'])
    if url.username or url.password or url.fragment or url.query:
        raise ValueError('Unexpected feed URL credentials/query/fragment')
    local = data.get('local_testing') is True
    if local:
        if url.scheme != 'http' or url.hostname != '127.0.0.1' or not url.port:
            raise ValueError('A test channel must use an explicit loopback port')
    elif data['feed_url'] != 'https://github.com/pengusto/naps2/releases/download/es60w-updates/appcast.xml':
        raise ValueError('Release channels must use the ES60W fork feed')
    if data.get('automatic_checks') and not data.get('published'):
        raise ValueError('Do not automatically query an unpublished channel')
    return local


def validate_inputs(distribution, configuration):
    here = Path(__file__).resolve().parent
    lock = json.loads((here / 'sparkle.lock.json').read_text())
    if hashlib.sha256(distribution.read_bytes()).hexdigest() != lock['distribution_sha256']:
        raise ValueError('Sparkle distribution hash mismatch')
    data = json.loads(configuration.read_text())
    local = validate_config(data)
    return data, local


def stage(app, distribution, configuration):
    here = Path(__file__).resolve().parent
    data, local = validate_inputs(distribution, configuration)
    contents = app / 'Contents'
    if not (contents / 'Helpers/ScanHelper.bundle/Contents/MacOS/scanimage').is_file():
        raise ValueError('The complete scan helper must be embedded first')
    framework_dir = contents / 'Frameworks'
    framework_dir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='es60w-sparkle-', dir='/private/tmp') as tmp:
        # Only this exact, pinned upstream release is accepted, never an arbitrary archive.
        subprocess.run(['tar', '-xf', str(distribution), '-C', tmp], check=True)
        framework = Path(tmp) / 'Sparkle.framework'
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(framework)], check=True)
        subprocess.run(['ditto', str(framework), str(framework_dir / 'Sparkle.framework')], check=True)
        subprocess.run(['clang', '-fobjc-arc', '-Wall', '-Wextra', '-Werror', '-dynamiclib',
            '-arch', 'arm64', '-mmacosx-version-min=14.0', '-framework', 'Cocoa',
            '-framework', 'Sparkle', '-F' + tmp, '-Wl,-rpath,@loader_path',
            '-install_name', '@rpath/libES60WUpdater.dylib', str(here / 'UpdaterBridge.m'),
            '-o', str(framework_dir / 'libES60WUpdater.dylib')], check=True)
    info_file = contents / 'Info.plist'
    info = plistlib.loads(info_file.read_bytes())
    release = json.loads((here.parent / 'release.json').read_text())
    info.update(SUFeedURL=data['feed_url'], SUPublicEDKey=data['public_ed_key'],
        SURequireSignedFeed=True, SUVerifyUpdateBeforeExtraction=True,
        SUEnableAutomaticChecks=bool(data.get('automatic_checks')),
        SUAutomaticallyUpdate=False, SUAllowsAutomaticUpdates=False,
        SUShowReleaseNotes=False, SUSendProfileInfo=False,
        CFBundleVersion=release['bundle_version'], ES60WReleaseVersion=release['version'],
        ES60WLocalUpdateTest=local, ES60WUpdateChannelPublished=bool(data.get('published')))
    if local:
        info['NSAppTransportSecurity'] = {'NSAllowsLocalNetworking': True}
    info_file.write_bytes(plistlib.dumps(info))
    resources = contents / 'Resources'
    (resources / 'es60w-updates.marker').write_text('Complete app and scan helper; Sparkle 2.10.1\n')
    (resources / 'es60w-update-channel.json').write_text(json.dumps(data, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app', type=Path)
    p.add_argument('--check-inputs-only', action='store_true')
    p.add_argument('--sparkle-distribution', type=Path, required=True)
    p.add_argument('--configuration', type=Path, required=True)
    a = p.parse_args()
    if a.check_inputs_only:
        validate_inputs(a.sparkle_distribution.resolve(strict=True), a.configuration.resolve(strict=True))
        return
    if not a.app:
        p.error('--app is required unless --check-inputs-only is supplied')
    stage(a.app.resolve(strict=True), a.sparkle_distribution.resolve(strict=True),
          a.configuration.resolve(strict=True))


if __name__ == '__main__':
    main()
