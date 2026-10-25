#!/usr/bin/env python3
"""Full macOS/registrar build and standalone local packaging. Never installs or scans."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--dotnet', type=Path, required=True)
    p.add_argument('--nuget-source', type=Path, help='Optional local NuGet feed from the source kit')
    p.add_argument('--nuget-packages', type=Path, help='Optional separate package cache for an offline rebuild')
    p.add_argument('--sparkle-distribution', type=Path, help='Optional pinned Sparkle archive for complete-app updates')
    p.add_argument('--updates-config', type=Path, help='Channel JSON; requires --sparkle-distribution')
    a = p.parse_args()
    if bool(a.sparkle_distribution) != bool(a.updates_config):
        p.error('Supply both --sparkle-distribution and --updates-config')
    here = Path(__file__).resolve().parent
    source_repo = here.parent
    if a.sparkle_distribution:
        subprocess.run([sys.executable, str(here / 'updates/stage-updater.py'),
            '--check-inputs-only', '--sparkle-distribution', str(a.sparkle_distribution.resolve(strict=True)),
            '--configuration', str(a.updates_config.resolve(strict=True))], check=True)
    out = a.output.resolve()
    if out.exists() or source_repo == out or source_repo in out.parents:
        p.error('Use a new output directory outside the checkout')
    # Resolve transitive native source inputs before the expensive registrar build.
    for name in ['helper-client/BundledScanImageLauncher.c',
                 'helper-client/TransportLogLauncher.c', 'scanner-button/ScannerButton.c',
                 'defaults/profiles.xml', 'defaults/appsettings.xml']:
        if not (here / 'tools' / name).is_file():
            p.error('Missing package source input: ' + name)
    subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-fsyntax-only',
        str(here / 'tools/helper-client/BundledScanImageLauncher.c')], check=True)
    licence_manifest = json.loads((here / 'licenses/MANIFEST.json').read_text())
    for name, expected in licence_manifest['files_sha256'].items():
        file = here / 'licenses' / name
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            p.error('Missing or changed licence input: ' + name)
    out.mkdir(parents=True)
    # Apple's trimmer can retain CodeView paths even when symbols are disabled.
    # A clean, neutral build root avoids personal paths without rewriting DLLs.
    repo = Path(tempfile.mkdtemp(prefix='naps2-es60w-build-', dir='/private/tmp'))
    shutil.copytree(source_repo, repo, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.git', 'bin', 'obj', '.scratch',
                        '__pycache__', 'downloads', 'dist', '.work'))
    (out / 'neutral-build-root.txt').write_text(str(repo) + '\n')
    env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_PROCESSOR_COUNT='1',
               DOTNET_CLI_UI_LANGUAGE='en', DOTNET_CLI_USE_MSBUILD_SERVER='0',
               MSBUILDDISABLENODEREUSE='1', COPYFILE_DISABLE='1')
    log = out / 'full-app-build.log'
    # Build the historical transitive dependency from the delivered preferred
    # sources, rather than guessing which commit produced an old NuGet binary.
    feed = out / 'source-built-feed'
    feed.mkdir()
    config = ET.Element('configuration')
    sources = ET.SubElement(config, 'packageSources')
    ET.SubElement(sources, 'clear')
    ET.SubElement(sources, 'add', key='source-built', value=str(feed))
    upstream_feed = str(a.nuget_source.resolve(strict=True)) if a.nuget_source else 'https://api.nuget.org/v3/index.json'
    ET.SubElement(sources, 'add', key='build-inputs', value=upstream_feed)
    nuget_config = out / 'NuGet.Config'
    ET.ElementTree(config).write(nuget_config, encoding='utf-8', xml_declaration=True)
    pack = [str(a.dotnet.resolve()), 'pack',
        str(repo / 'es60w/dependencies/SimpleBase/SimpleBase.Es60w.csproj'),
        '-c', 'Release', '--disable-build-servers', '-maxcpucount:1',
        '-p:BuildInParallel=false', '-p:UseSharedCompilation=false',
        '-p:DebugSymbols=false', '-p:DebugType=None',
        '-p:RestoreConfigFile=' + str(nuget_config), '-o', str(feed)]
    if a.nuget_packages:
        pack.append('-p:RestorePackagesPath=' + str(a.nuget_packages.resolve()))
    with (out / 'source-built-dependency.log').open('wb') as stream:
        subprocess.run(pack, cwd=repo, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
    command = [str(a.dotnet.resolve()), 'build', 'NAPS2.App.Mac/NAPS2.App.Mac.csproj',
        '-c', 'Release', '-r', 'osx-arm64', '--nologo', '--disable-build-servers', '--no-incremental',
        '-maxcpucount:1', '-p:BuildInParallel=false', '-p:UseSharedCompilation=false',
        '-p:SupportedOSPlatformVersion=14.0', '-p:EnableCodeSigning=false',
        '-p:RestoreIgnoreFailedSources=true', '-p:DebugSymbols=false', '-p:DebugType=None',
        '-p:TrimmerRemoveSymbols=true', '-p:PathMap=' + str(repo) + '=/src/naps2']
    command.append('-p:RestoreConfigFile=' + str(nuget_config))
    if a.nuget_packages:
        command.append('-p:RestorePackagesPath=' + str(a.nuget_packages.resolve()))
    with log.open('wb') as stream:
        r = subprocess.run(command, cwd=repo, env=env, stdout=stream, stderr=subprocess.STDOUT)
    if r.returncode or 'Build succeeded.' not in log.read_text().splitlines():
        raise RuntimeError('Full build failed or incomplete; see ' + str(log))
    print('Full app/static registrar build passed', flush=True)
    native = a.native_build.resolve()
    manifest = json.loads((native / 'result.json').read_text())
    overlay = out / 'overlay'
    helper = overlay / 'Contents/Helpers/ScanHelper.bundle/Contents'
    shutil.copytree(native / 'helper', helper)
    (helper / 'Info.plist').write_bytes(plistlib.dumps({
        'CFBundleIdentifier': 'de.pengusto.naps2.es60w.scanhelper',
        'CFBundleName': 'ScanHelper', 'CFBundleExecutable': 'scanimage',
        'CFBundlePackageType': 'BNDL', 'CFBundleVersion': '1',
        'CFBundleShortVersionString': '1.4.0', 'LSMinimumSystemVersion': '14.0'}))
    (helper / 'Resources/staging-input-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    resources = overlay / 'Contents/Resources'
    resources.mkdir(parents=True)
    (resources / 'external-scanimage.marker').write_text('Separate bundled free scanimage helper.\n')
    app = out / 'NAPS2 ES60W.app'
    built = repo / 'NAPS2.App.Mac/bin/Release/net10.0-macos/osx-arm64/NAPS2.app'
    package_command = [sys.executable, str(here / 'tools/package-helper-app.py'),
        '--source-app', str(built), '--overlay', str(overlay), '--destination', str(app),
        '--entitlements', str(repo / 'NAPS2.App.Mac/Entitlements.plist'),
        '--scanner-button-header', str(native / 'prefix/include/libusb-1.0/libusb.h'),
        '--report', str(out / 'package.json')]
    if a.sparkle_distribution:
        package_command += ['--sparkle-distribution', str(a.sparkle_distribution.resolve(strict=True)),
                            '--updates-config', str(a.updates_config.resolve(strict=True))]
    subprocess.run(package_command, check=True)
    result = {'architecture': 'arm64', 'release_version': '8.5.1-es60w.4-local' if a.updates_config else '8.5.1-es60w.3',
              'complete_app_updates_embedded': bool(a.updates_config),
              'full_app_and_static_registrar_rebuilt': True,
              'helper_libusb_jpeg_built_from_pinned_sources': True,
              'build_log_sha256': hashlib.sha256(log.read_bytes()).hexdigest(),
              'workers': 1, 'installed': False, 'hardware_scans': 0,
              'personal_build_paths_permitted_in_app': False,
              'neutral_build_root': str(repo),
              'developer_id_signed': False, 'notarized': False,
              'simplebase_built_from_delivered_sources': True,
              'distribution_channel': 'independent ad-hoc-signed prerelease'}
    (out / 'build-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(str(app), flush=True)


if __name__ == '__main__':
    main()
