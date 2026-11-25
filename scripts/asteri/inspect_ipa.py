"""Inspect compiled IPA contents without trusting filenames or ARM64 alone."""
import argparse
import hashlib
import json
import plistlib
import re
import stat
import struct
import zipfile
from pathlib import Path, PurePosixPath

ARM64 = 0x0100000C
MACH64 = b'\xcf\xfa\xed\xfe'


def macho_slices(data):
    if data[:4] == MACH64:
        if len(data) < 32:
            raise ValueError('Truncated Mach-O header')
        _, cpu, _, kind, count, commands_size, _, _ = struct.unpack_from('<8I', data)
        end = 32 + commands_size
        if end > len(data) or count > commands_size // 8:
            raise ValueError('Invalid Mach-O command table')
        cursor = 32
        platforms = set()
        for _ in range(count):
            if cursor + 8 > end:
                raise ValueError('Truncated load command')
            command, size = struct.unpack_from('<II', data, cursor)
            if size < 8 or cursor + size > end:
                raise ValueError('Invalid Mach-O load command')
            if command == 0x32:  # LC_BUILD_VERSION
                if size < 24:
                    raise ValueError('Truncated LC_BUILD_VERSION')
                platforms.add(struct.unpack_from('<I', data, cursor + 8)[0])
            elif command == 0x25:  # LC_VERSION_MIN_IPHONEOS
                if size < 16:
                    raise ValueError('Truncated LC_VERSION_MIN_IPHONEOS')
                platforms.add(2)
            cursor += size
        if cursor != end:
            raise ValueError('Inconsistent Mach-O command table')
        return [{'cpu': cpu, 'kind': kind, 'platforms': sorted(platforms)}]
    if data[:4] in {b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'}:
        if len(data) < 8:
            raise ValueError('Truncated universal header')
        count = struct.unpack_from('>I', data, 4)[0]
        wide = data[:4] == b'\xca\xfe\xba\xbf'
        size = 32 if wide else 20
        table_end = 8 + count * size
        if not count or count > 32 or table_end > len(data):
            raise ValueError('Invalid universal header')
        slices, regions = [], []
        for index in range(count):
            entry = 8 + index * size
            cpu = struct.unpack_from('>I', data, entry)[0]
            offset, length = struct.unpack_from('>QQ' if wide else '>II', data, entry + 8)
            if offset < table_end or not length or offset + length > len(data):
                raise ValueError('Invalid universal slice')
            if any(offset < high and offset + length > low for low, high in regions):
                raise ValueError('Overlapping universal slices')
            regions.append((offset, offset + length))
            child = macho_slices(data[offset:offset + length])
            if len(child) != 1 or child[0]['cpu'] != cpu:
                raise ValueError('Universal CPU/header mismatch')
            slices.extend(child)
        return slices
    raise ValueError('Executable is not a supported 64-bit Mach-O binary')


def checked_members(archive):
    names = set()
    for member in archive.infolist():
        name = member.filename
        path = PurePosixPath(name)
        if (name in names or '\\' in name or path.is_absolute() or '..' in path.parts
                or re.match(r'^[A-Za-z]:', name)):
            raise ValueError('Unsafe or duplicate ZIP entry')
        if stat.S_ISLNK(member.external_attr >> 16):
            # The iOS app uses flat frameworks, so no symlink is needed here.
            raise ValueError('Unexpected symlink in IPA')
        names.add(name)
    return names


def inspect_ipa(path, mode='unsigned', expected_bundle_id=None):
    platform = 7 if mode == 'simulator' else 2
    result = {'mode': mode, 'device_tested': False, 'binaries': [], 'bundles': []}
    with zipfile.ZipFile(path) as archive:
        names = checked_members(archive)
        apps = sorted({n.split('/')[1] for n in names
                       if re.match(r'^Payload/[^/]+\.app/', n)})
        if len(apps) != 1:
            raise ValueError('IPA must contain exactly one Payload/*.app')
        root = f'Payload/{apps[0]}'
        plists = sorted(n for n in names if n.endswith('/Info.plist') and
                        re.search(r'\.(?:app|appex|framework)/Info.plist$', n))
        if f'{root}/Info.plist' not in plists:
            raise ValueError('Main Info.plist is missing')
        executable_names = set()
        bundle_ids = set()
        for name in plists:
            if not name.startswith(root + '/'):
                raise ValueError('Bundle outside the main app')
            info = plistlib.loads(archive.read(name))
            bundle = name[:-len('/Info.plist')]
            executable = info.get('CFBundleExecutable', '')
            if not re.fullmatch(r'[A-Za-z0-9_.+-]+', executable):
                raise ValueError('Invalid CFBundleExecutable')
            binary = f'{bundle}/{executable}'
            if binary not in names:
                raise ValueError(f'Missing bundle executable: {binary}')
            if not archive.getinfo(binary).external_attr >> 16 & 0o111:
                raise ValueError(f'Executable permissions missing: {binary}')
            identifier = info.get('CFBundleIdentifier', '')
            if not identifier or identifier in bundle_ids:
                raise ValueError('Missing or duplicate bundle ID')
            bundle_ids.add(identifier)
            if bundle == root:
                if expected_bundle_id and identifier != expected_bundle_id:
                    raise ValueError('Unexpected main bundle ID')
                if info.get('CFBundlePackageType') != 'APPL':
                    raise ValueError('Main bundle is not an application')
                expected = 'iPhoneSimulator' if platform == 7 else 'iPhoneOS'
                if expected not in info.get('CFBundleSupportedPlatforms', []):
                    raise ValueError('Wrong bundle platform')
                result['bundle_id'] = identifier
                result['version'] = info.get('CFBundleShortVersionString')
                result['build'] = info.get('CFBundleVersion')
            elif bundle.endswith('.appex'):
                main_id = plistlib.loads(archive.read(f'{root}/Info.plist'))['CFBundleIdentifier']
                if not identifier.startswith(main_id + '.'):
                    raise ValueError('Extension bundle ID does not belong to the app')
            executable_names.add(binary)
            result['bundles'].append({'path': bundle, 'bundle_id': identifier})
        binaries = executable_names | {n for n in names if n.endswith('.dylib')}
        for name in sorted(binaries):
            slices = macho_slices(archive.read(name))
            arm = [s for s in slices if s['cpu'] == ARM64]
            if len(arm) != 1 or any(s['platforms'] != [platform] for s in slices):
                raise ValueError(f'Expected ARM64 platform {platform}: {name}')
            expected_kind = 6 if '.framework/' in name or name.endswith('.dylib') else 2
            if arm[0]['kind'] != expected_kind:
                raise ValueError(f'Wrong Mach-O file type: {name}')
            result['binaries'].append({'path': name, 'slices': slices})
        profiles = [n for n in names if n.endswith('/embedded.mobileprovision')]
        if mode == 'unsigned' and profiles:
            raise ValueError('Unsigned artifact unexpectedly contains provisioning profiles')
        if mode == 'signed':
            for bundle in result['bundles']:
                if bundle['path'].endswith(('.app', '.appex')) and bundle['path'] + '/embedded.mobileprovision' not in names:
                    raise ValueError('Signed app or extension lacks an embedded profile')
    with Path(path).open('rb') as executable_file:
        result['sha256'] = hashlib.file_digest(executable_file, 'sha256').hexdigest()
    result['size_bytes'] = Path(path).stat().st_size
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ipa', type=Path)
    parser.add_argument('--mode', choices=['unsigned', 'signed', 'simulator'], default='unsigned')
    parser.add_argument('--bundle-id')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    inspection = inspect_ipa(args.ipa, args.mode, args.bundle_id)
    output = json.dumps(inspection, indent=2) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output)
