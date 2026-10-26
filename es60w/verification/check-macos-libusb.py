#!/usr/bin/env python3
"""Reject the SDK-only pipe2 dependency without loading USB code or scanning."""
import argparse
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library')
    args = parser.parse_args()
    imports = subprocess.check_output(
        ['xcrun', 'dyld_info', '-imports', args.library], text=True)
    if re.search(r'\b_pipe2\b', imports):
        parser.exit(1, 'FAIL: libusb imports pipe2, unavailable on supported macOS.\n')
    if not re.search(r'\b_pipe\b', imports) or not re.search(r'\b_fcntl\b', imports):
        parser.exit(1, 'FAIL: expected pipe/fcntl fallback imports are missing.\n')
    print('PASS: pipe/fcntl fallback; no pipe2 import. No USB code executed.')


if __name__ == '__main__':
    main()
