"""Ephemeral certificate import and explicit bundle/profile verification on macOS."""
import base64
import datetime
import fnmatch
import io
import json
import os
import plistlib
import secrets
import subprocess
import zipfile
from pathlib import Path
from inspect_ipa import checked_members


def security(*args):
    result = subprocess.run(['security', *args], capture_output=True)
    if result.returncode:
        # Arguments can contain passwords: never propagate CalledProcessError.
        raise RuntimeError('A security/keychain operation failed; check signing material and password')
    return result.stdout


def prepare_signing(private):
    source = private / 'signing'
    source.mkdir(parents=True, exist_ok=True)
    try:
        payload = base64.b64decode(os.environ['IOS_SIGNING_ARCHIVE_BASE64'], validate=True)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            checked_members(archive)
            if sum(i.file_size for i in archive.infolist()) > 100 * 1024**2:
                raise ValueError('Signing archive exceeds 100 MiB')
            if any(i.filename.split('/')[0] not in {'profiles', 'certs'} for i in archive.infolist()):
                raise ValueError('Signing ZIP must contain only profiles/ and certs/')
            archive.extractall(source)
    except (KeyError, ValueError, zipfile.BadZipFile):
        raise ValueError('Invalid IOS_SIGNING_ARCHIVE_BASE64 ZIP') from None
    certs = sorted((source / 'certs').glob('*.p12'))
    profiles = sorted((source / 'profiles').glob('*.mobileprovision'))
    if not certs or not profiles:
        raise ValueError('Signing archive requires certs/*.p12 and profiles/*.mobileprovision')
    keychain = private / 'asteri.keychain-db'
    previous = [str(p) for p in security('list-keychains', '-d', 'user').decode().split('"')
                if p.strip() and p.strip() != '\n']
    previous = [p.strip() for p in previous if p.strip().startswith('/')]
    (private / 'keychain-state.json').write_text(json.dumps({'previous': previous, 'keychain': str(keychain)}))
    password = secrets.token_urlsafe(32)
    security('create-keychain', '-p', password, str(keychain))
    security('set-keychain-settings', '-lut', '21600', str(keychain))
    security('unlock-keychain', '-p', password, str(keychain))
    security('list-keychains', '-d', 'user', '-s', str(keychain), *previous)
    for cert in certs:
        security('import', str(cert), '-k', str(keychain), '-P',
                 os.getenv('IOS_CERTIFICATE_PASSWORD', ''), '-T', '/usr/bin/codesign', '-T', '/usr/bin/security')
    security('set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:',
             '-s', '-k', password, str(keychain))
    return source


def verify_profile(profile, entitlements, team_id, bundle_id):
    expiry = profile.get('ExpirationDate')
    if not isinstance(expiry, datetime.datetime) or expiry.replace(tzinfo=datetime.timezone.utc) <= datetime.datetime.now(datetime.timezone.utc):
        raise ValueError('Provisioning profile is missing an expiration or has expired')
    allowed = profile.get('Entitlements', {})
    actual_id = entitlements.get('application-identifier', '')
    if (team_id not in profile.get('TeamIdentifier', []) or actual_id != f'{team_id}.{bundle_id}'
            or not fnmatch.fnmatchcase(actual_id, allowed.get('application-identifier', ''))):
        raise ValueError('Profile, Team ID, bundle ID and executable entitlements do not match')
    if entitlements.get('com.apple.developer.team-identifier') != team_id:
        raise ValueError('Executable has an unexpected Team ID')
    for key, value in entitlements.items():
        if key not in allowed:
            raise ValueError(f'Entitlement is not permitted by profile: {key}')
        permitted = allowed[key]
        if isinstance(value, list):
            if not isinstance(permitted, list) or any(not any(
                    isinstance(v, str) and isinstance(p, str) and fnmatch.fnmatchcase(v, p)
                    for p in permitted) for v in value):
                raise ValueError(f'Profile does not permit entitlement values: {key}')
        elif isinstance(value, str) and isinstance(permitted, str):
            if not fnmatch.fnmatchcase(value, permitted):
                raise ValueError(f'Profile does not permit entitlement value: {key}')
        elif value != permitted:
            raise ValueError(f'Profile does not permit entitlement value: {key}')


def verify_signing(ipa, private, inspection, team_id):
    stage = private / 'verify-signed'
    stage.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ditto', '-x', '-k', str(ipa), str(stage)], check=True)
    for bundle in inspection['bundles']:
        path = stage / bundle['path']
        subprocess.run(['codesign', '--verify', '--strict', str(path)], check=True)
        if path.suffix in {'.app', '.appex'}:
            profile = plistlib.loads(security('cms', '-D', '-i', str(path / 'embedded.mobileprovision')))
            result = subprocess.run(['codesign', '-d', '--entitlements', ':-', str(path)], capture_output=True, check=True)
            entitlements = plistlib.loads(result.stdout)
            verify_profile(profile, entitlements, team_id, bundle['bundle_id'])
    for binary in inspection['binaries']:
        subprocess.run(['codesign', '--verify', '--strict', str(stage / binary['path'])], check=True)
    inspection['codesign_verified'] = True
    inspection['profile_entitlements_verified'] = True


def cleanup_signing(private):
    state_file = private / 'keychain-state.json'
    if state_file.exists():
        state = json.loads(state_file.read_text())
        security('list-keychains', '-d', 'user', '-s', *state['previous'])
        keychain = Path(state['keychain'])
        if keychain.parent.resolve() != private.resolve():
            raise ValueError('Refusing to remove a keychain outside private build storage')
        if keychain.exists():
            security('delete-keychain', str(keychain))
