#!/usr/bin/env python3
"""Thin CI orchestration around Telegram's official build. No emulation or fake IPA."""
import json
import os
import platform
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

from config import validate_config
from inspect_ipa import inspect_ipa

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'build/asteri'
PRIVATE = ROOT / 'build-input/asteri'


def capture(*command):
    return subprocess.check_output(command, cwd=ROOT, text=True).strip()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def configuration():
    return validate_config(os.environ.get('TELEGRAM_BUILD_CONFIGURATION'),
                           os.environ.get('BUILD_MODE', 'unsigned'))


def preflight():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise ValueError('Apple SDK work requires an ARM64 macOS runner (xcode-27)')
    versions = json.loads((ROOT / 'versions.json').read_text())
    xcode = Path('/Applications') / f'Xcode_{versions["xcode"]}.app/Contents/Developer'
    if not xcode.is_dir():
        raise ValueError(f'Pinned Xcode {versions["xcode"]} is absent; do not bypass version checks')
    subprocess.run(['sudo', 'xcode-select', '--switch', str(xcode)], check=True)
    actual = capture('xcodebuild', '-version')
    if actual.splitlines()[0] != f'Xcode {versions["xcode"]}':
        raise ValueError('Selected Xcode does not match versions.json')
    free = shutil.disk_usage(ROOT).free
    report = {'versions': versions, 'xcode': actual, 'macos': capture('sw_vers'),
              'machine': platform.machine(), 'free_bytes': free,
              'source_commit': capture('git', 'rev-parse', 'HEAD'),
              'run_url': f'https://github.com/{os.getenv("GITHUB_REPOSITORY", "")}/actions/runs/{os.getenv("GITHUB_RUN_ID", "")}',
              'mode': os.getenv('BUILD_MODE', 'unsigned'), 'device_tested': False}
    write_json(OUTPUT / 'provenance.json', report)
    print(json.dumps(report, indent=2), flush=True)
    if free < 12 * 1024**3:
        raise ValueError('Less than 12 GiB free before dependency checkout; insufficient for this build')
    configuration()
    if os.getenv('BUILD_MODE') == 'signed' and not os.getenv('IOS_SIGNING_ARCHIVE_BASE64'):
        raise ValueError('Signed mode requires IOS_SIGNING_ARCHIVE_BASE64')


def prepare():
    config = configuration()
    PRIVATE.mkdir(parents=True, exist_ok=True)
    config_path = PRIVATE / 'configuration.json'
    write_json(config_path, config)
    config_path.chmod(0o600)
    cache = Path.home() / 'Library/Caches/asteri-bazel-repository'
    cache.mkdir(parents=True, exist_ok=True)
    flags = [f'build --repository_cache={cache}', 'build --jobs=2']
    mode = os.getenv('BUILD_MODE', 'unsigned')
    if mode != 'signed':
        flags += ['build --//Telegram:disableProvisioningProfiles']
    if mode == 'simulator':
        # Simulator ad-hoc signing needs no Apple credential and carries the app's
        # real entitlements. Omitting signing loses App Groups during installation.
        flags += ['build --features=apple.codesign_frameworks_without_provisioning_profile']
    if mode == 'unsigned':
        from unsigned import apply
        patch = apply(ROOT / 'build-system/bazel-rules/rules_apple/apple/internal/ios_rules.bzl')
        write_json(OUTPUT / 'unsigned-rules-patch.json', patch)
        flags += ['build --features=disable_legacy_signing',
                  'build --features=asteri.unsigned_archive']
    if os.getenv('DISABLE_EXTENSIONS', 'false').lower() == 'true':
        flags += ['build --//Telegram:disableExtensions']
    (ROOT / 'build-input/asteri.bazelrc').write_text('\n'.join(flags) + '\n', encoding='utf-8')
    (OUTPUT / 'effective-bazelrc.txt').write_text('\n'.join(flags) + '\n', encoding='utf-8')
    return config, config_path


def logged(command, name, redactions=()):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / name).open('w', encoding='utf-8') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, errors='replace', bufsize=1)
        for line in process.stdout:
            for secret in redactions:
                if secret:
                    line = line.replace(secret, '[REDACTED]')
            log.write(line)
            log.flush()
            print(line, end='', flush=True)
        code = process.wait()
    if code:
        raise RuntimeError(f'{name}: process failed with exit status {code}; full log retained')


def build():
    preflight()
    config, path = prepare()
    mode = os.getenv('BUILD_MODE', 'unsigned')
    command = [sys.executable, '-u', 'build-system/Make/Make.py', 'build',
               '--configurationPath', str(path),
               '--buildNumber', str(int(os.getenv('GITHUB_RUN_NUMBER', '1'))),
               '--configuration', 'debug_sim_arm64' if mode == 'simulator' else 'release_arm64']
    if mode == 'signed':
        from signing import prepare_signing
        signing_dir = prepare_signing(PRIVATE)
        command += ['--codesigningInformationPath', str(signing_dir)]
    else:
        command += ['--xcodeManagedCodesigning']
    # Compile and check the actual generated metadata before the expensive app.
    logged(command + ['--target', '//Telegram:UrlTypesInfoPlist'],
           'metadata.log', (config['api_hash'],))
    metadata = plistlib.loads((ROOT / 'bazel-bin/Telegram/UrlTypesInfoPlist.plist').read_bytes())
    schemes = [scheme for entry in metadata.get('CFBundleURLTypes', [])
               for scheme in entry.get('CFBundleURLSchemes', [])]
    if config['app_specific_url_scheme'] not in schemes:
        raise ValueError('Generated URL metadata is missing the configured app URL scheme')
    write_json(OUTPUT / 'metadata-inspection.json', {'url_schemes': schemes})
    ipa = ROOT / 'bazel-bin/Telegram/Telegram.ipa'
    unverified = OUTPUT / 'unverified-compiled.ipa'
    try:
        logged(command, 'build.log', (config['api_hash'],))
    finally:
        # Preserve a real compiler output even if the wrapper's postbuild check
        # fails. It remains explicitly unverified and is never a release asset.
        if ipa.is_file():
            shutil.copy2(ipa, unverified)
    if not unverified.is_file():
        raise ValueError('Official build did not produce bazel-bin/Telegram/Telegram.ipa')
    inspection = inspect_ipa(unverified, mode, config['bundle_id'], config['app_specific_url_scheme'])
    if mode == 'signed':
        from signing import verify_signing
        verify_signing(unverified, PRIVATE, inspection, config['team_id'])
    inspection['extensions_disabled'] = os.getenv('DISABLE_EXTENSIONS', 'false').lower() == 'true'
    write_json(OUTPUT / 'ipa-inspection.json', inspection)
    target = OUTPUT / 'Asteri.ipa'
    unverified.replace(target)
    (OUTPUT / 'SHA256SUMS').write_text(f'{inspection["sha256"]}  Asteri.ipa\n', encoding='utf-8')
    print(f'Compiled and structurally verified {mode} artifact ({inspection["size_bytes"]} bytes).')


def test():
    if os.getenv('BUILD_MODE') != 'simulator':
        raise ValueError('The simulator test stage requires a simulator build')
    config = configuration()
    versions = json.loads((ROOT / 'versions.json').read_text())
    bazel_version = versions['bazel'].split(':')[0]
    bazel = ROOT / f'build-input/bazel-{bazel_version}-darwin-arm64'
    # Real native upstream regression test; no Android or GUI hooks.
    logged([str(bazel), 'test', '//submodules/UrlWhitelist:UrlWhitelistTests',
            '--test_output=all'], 'native-tests.log', (config['api_hash'],))
    from simulator import smoke
    smoke(OUTPUT / 'Asteri.ipa', config['bundle_id'], PRIVATE, OUTPUT)


def cleanup():
    if platform.system() == 'Darwin':
        from signing import cleanup_signing
        cleanup_signing(PRIVATE)
    # Also erase generated copies of API credentials made by the official wrapper.
    for candidate in (PRIVATE, ROOT / 'build-input/configuration-repository',
                      ROOT / 'build-input/configuration-repository-workdir'):
        if candidate.exists():
            shutil.rmtree(candidate)
    (ROOT / 'build-input/asteri.bazelrc').unlink(missing_ok=True)
    from unsigned import restore
    restore(ROOT / 'build-system/bazel-rules/rules_apple/apple/internal/ios_rules.bzl')


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in {'preflight', 'build', 'test', 'cleanup'}:
            raise ValueError('Usage: build.py preflight|build|test|cleanup')
        os.chdir(ROOT)
        globals()[sys.argv[1]]()
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        # Never include secret-bearing signing command arguments in an exception.
        message = str(error) if isinstance(error, (ValueError, RuntimeError)) else type(error).__name__
        print(f'::error::{message}', file=sys.stderr)
        sys.exit(1)
