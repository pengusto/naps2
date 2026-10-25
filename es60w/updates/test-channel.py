#!/usr/bin/env python3
"""Negative checks for release channel inputs; no app, network or keychain access."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('stage_updater', here / 'stage-updater.py')
stage = importlib.util.module_from_spec(spec); spec.loader.exec_module(stage)


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((here / 'channel.json').read_text())

    def test_reserved_release_channel(self):
        self.assertFalse(stage.validate_config(self.valid))

    def test_explicit_loopback_fixture(self):
        self.valid.update(local_testing=True, feed_url='http://127.0.0.1:54321/appcast.xml')
        self.assertTrue(stage.validate_config(self.valid))

    def test_invalid_release_urls(self):
        for url in ['http://github.com/pengusto/naps2/releases/download/es60w-updates/appcast.xml',
                    'https://github.com/other/naps2/releases/download/es60w-updates/appcast.xml',
                    'https://user:password@github.com/pengusto/naps2/releases/download/es60w-updates/appcast.xml',
                    self.valid['feed_url'] + '?token=bad', self.valid['feed_url'] + '#fragment',
                    'file:///tmp/appcast.xml', 'http://127.0.0.1:1234/appcast.xml']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                stage.validate_config(dict(self.valid, feed_url=url))

    def test_local_mode_cannot_reach_other_hosts(self):
        for url in ['http://192.168.1.10:1234/appcast.xml', 'http://0.0.0.0:1234/appcast.xml',
                    'http://127.0.0.1/appcast.xml', 'https://github.com/appcast.xml']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                stage.validate_config(dict(self.valid, local_testing=True, feed_url=url))

    def test_public_key_shape(self):
        for key in ['', 'invalid-base64', 'YQ==']:
            with self.subTest(key=key), self.assertRaises(ValueError):
                stage.validate_config(dict(self.valid, public_ed_key=key))

    def test_no_automatic_query_of_unpublished_feed(self):
        with self.assertRaises(ValueError):
            stage.validate_config(dict(self.valid, automatic_checks=True, published=False))

    def test_flags_are_not_strings_or_numbers(self):
        for flag in ['automatic_checks', 'local_testing', 'published']:
            for value in ['false', 1, None]:
                with self.subTest(flag=flag, value=value), self.assertRaises(ValueError):
                    stage.validate_config(dict(self.valid, **{flag: value}))

    def test_schema(self):
        for schema in [True, 0, '1', 2]:
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                stage.validate_config(dict(self.valid, schema=schema))

    def test_wrong_framework_archive_rejected_before_app_access(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'wrong.tar.xz'; archive.write_bytes(b'wrong archive')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                stage.stage(Path(folder) / 'absent.app', archive, here / 'channel.json')

    def test_updater_export_requires_matching_sparkle_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            app = Path(folder) / 'stub.app'
            marker = app / 'Contents/Resources/es60w-updates.marker'
            marker.parent.mkdir(parents=True); marker.write_text('test marker')
            result = subprocess.run([sys.executable, str(here.parent / 'prepare-local-release.py'),
                '--app', str(app), '--downloads', folder, '--package-inputs', folder,
                '--output', str(Path(folder) / 'out')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('requires --sparkle-inputs', result.stderr)
            self.assertFalse((Path(folder) / 'out').exists())


if __name__ == '__main__':
    unittest.main()
