#!/usr/bin/env python3
"""Test the actual app's PNG import/PDF export with EXACTLY ZERO scan requests.

Creates a synthetic PNG; requires no external Python packages. Denies network,
Epson installation reads and normal NAPS2 profile reads/writes for this process.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--app', type=Path, required=True)
p.add_argument('--output', type=Path, required=True, help='NEW local directory')
p.add_argument('--prepare-only', action='store_true', help='Write synthetic fixture only; execute no app or helper')
a = p.parse_args(); out = a.output.resolve(); app = a.app.resolve()
out.mkdir(parents=True, exist_ok=False)
def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
w, h = 600, 300
pixels = b''.join(b'\0' + b''.join(bytes((240, 240, 240) if x < 30 or x >= 570 or y < 30 or y >= 270
                 else ((220, 20, 20) if x < 300 else (20, 80, 220))) for x in range(w)) for y in range(h))
fixture = out / 'synthetic.png'
fixture.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                    + chunk(b'pHYs', struct.pack('>IIB', 11811, 11811, 1))
                    + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b''))
if a.prepare_only:
    print(json.dumps({'fixture': str(fixture), 'pixels': [w, h], 'dpi': 300, 'app_executed': False, 'scan_requests': 0}))
    raise SystemExit(0)
daily = str(Path.home() / '.config/naps2')
blocked = ['/Applications/Epson Software', '/Library/Image Capture', '/Library/Application Support/EPSON', daily]
policy = '(version 1)(allow default)(deny iokit-open)(deny network-outbound (remote ip "*:*"))(deny file-read* ' + ' '.join(
    '(subpath ' + json.dumps(s) + ')' for s in blocked) + ')(deny file-write* (subpath ' + json.dumps(daily) + '))'
sb = out / 'offline.sb'; sb.write_text(policy + '\n')
env = dict(os.environ, NAPS2_TEST_DATA=str(out / 'data'), PATH='/usr/bin:/bin')
for key in ('DOTNET_ROOT', 'NAPS2_TEST_DEPS'): env.pop(key, None)
# Mac image operations need the UI dispatcher; --progress initializes it.
# In AutomatedScanning.Run, Number > 0 gates PerformScan. Never omit -n 0.
command = ['/usr/bin/sandbox-exec', '-f', str(sb), str(app / 'Contents/MacOS/NAPS2'),
           'cli', '-i', str(fixture), '-o', str(out / 'synthetic.pdf'), '-n', '0',
           '--noprofile', '--disableocr', '--verbose', '--progress']
run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45)
(out / 'stdout.log').write_text(run.stdout); (out / 'stderr.log').write_text(run.stderr)
run.check_returncode()
pdf = out / 'synthetic.pdf'
if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):
    raise RuntimeError('No PDF generated')
r = {'scan_requests': 0, 'synthetic_input_pixels': [w, h], 'input_dpi': 300,
     'pdf_header_valid': True, 'pdf_bytes': pdf.stat().st_size,
     'network_denied': True, 'epson_and_daily_paths_denied': True,
     'path_without_dotnet': True, 'hardware_scan': False}
(out / 'result.json').write_text(json.dumps(r, indent=2) + '\n')
print(json.dumps(r, indent=2))
