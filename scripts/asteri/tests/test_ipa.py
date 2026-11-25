"""Synthetic headers test the inspector only; they are never build/release artifacts."""
import plistlib
import stat
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from inspect_ipa import ARM64, inspect_ipa, macho_slices


def header(platform=2, cpu=ARM64, kind=2):
    return struct.pack('<8I', 0xFEEDFACF, cpu, 0, kind, 1, 24, 0, 0) + struct.pack('<6I', 0x32, 24, platform, 0, 0, 0)


class IpaInspectionTests(unittest.TestCase):
    def create_fixture(self, path, binary=None, extras=None, executable=True):
        info = dict(CFBundleIdentifier='org.example.asteri', CFBundleExecutable='Asteri',
                    CFBundlePackageType='APPL', CFBundleSupportedPlatforms=['iPhoneOS'],
                    CFBundleShortVersionString='1.0', CFBundleVersion='1', MinimumOSVersion='15.0',
                    CFBundleURLTypes=[{'CFBundleURLSchemes': ['asteri']}])
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('Payload/Asteri.app/Info.plist', plistlib.dumps(info))
            member = zipfile.ZipInfo('Payload/Asteri.app/Asteri')
            member.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
            archive.writestr(member, header() if binary is None else binary)
            for name, data in (extras or {}).items():
                archive.writestr(name, data)

    def test_reads_device_header(self):
        self.assertEqual(macho_slices(header())[0]['platforms'], [2])

    def test_rejects_bad_and_truncated_macho(self):
        for binary in (b'fake executable', header()[:30], header()[:40]):
            with self.subTest(binary=binary), self.assertRaises(ValueError):
                macho_slices(binary)

    def test_rejects_simulator_arm64_and_non_arm64(self):
        for binary in (header(platform=7), header(cpu=0x01000007), header(kind=6)):
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'inspector-test.zip'
                self.create_fixture(path, binary=binary)
                with self.assertRaises(ValueError):
                    inspect_ipa(path)

    def test_rejects_unsafe_paths_unsigned_profiles_missing_permissions(self):
        for extras, executable in (({'../escape': b'x'}, True),
                                   ({'Payload/Asteri.app/embedded.mobileprovision': b'x'}, True),
                                   ({}, False)):
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'inspector-test.zip'
                self.create_fixture(path, extras=extras, executable=executable)
                with self.assertRaises(ValueError):
                    inspect_ipa(path)

    def test_report_and_expected_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'inspector-test.zip'
            self.create_fixture(path)
            report = inspect_ipa(path, expected_bundle_id='org.example.asteri')
            self.assertEqual(report['bundle_id'], 'org.example.asteri')
            self.assertFalse(report['device_tested'])
            self.assertEqual(len(report['sha256']), 64)
            with self.assertRaises(ValueError):
                inspect_ipa(path, expected_bundle_id='org.wrong.id')
            with self.assertRaises(ValueError):
                inspect_ipa(path, expected_url_scheme='missing')
