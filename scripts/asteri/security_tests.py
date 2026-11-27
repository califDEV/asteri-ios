#!/usr/bin/env python3
"""Run native scope tests against the production passcode sources on macOS."""
import json
import sys
import xml.etree.ElementTree as ET

from build import ROOT, OUTPUT, preflight, prepare, logged, write_json


def main():
    preflight()
    config, path = prepare()
    logged([sys.executable, '-u', 'build-system/Make/Make.py', 'build',
            '--configurationPath', str(path), '--buildNumber', '1',
            '--configuration', 'debug_sim_arm64', '--xcodeManagedCodesigning',
            '--target', '//Telegram:UrlTypesInfoPlist'], 'security-configuration.log', (config['api_hash'],))
    versions = json.loads((ROOT / 'versions.json').read_text())
    bazel_version = versions['bazel'].split(':')[0]
    bazel = ROOT / f'build-input/bazel-{bazel_version}-darwin-arm64'
    logged([str(bazel), 'test', '//submodules/PasscodeCore:PasscodeStorageScopeTests',
            '--test_output=all'], 'security-tests.log', (config['api_hash'],))
    result = ROOT / 'bazel-testlogs/submodules/PasscodeCore/PasscodeStorageScopeTests/test.xml'
    cases = ET.parse(result).findall('.//testcase')
    if len(cases) < 5 or any(c.find('failure') is not None or c.find('error') is not None for c in cases):
        raise ValueError('Expected at least five passing native credential-scope scenarios')
    write_json(OUTPUT / 'security-tests.json', {
        'tests': [c.attrib for c in cases], 'passed': True, 'device_tested': False,
        'source_files': ['Passcode.swift', 'PasscodeCrypto.swift', 'PasscodeKeychainScope.swift'],
    })


if __name__ == '__main__':
    main()
