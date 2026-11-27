"""Login-free launch smoke test. Does not assert Telegram account functionality."""
import json
import plistlib
import signal
import subprocess
import time
from inspect_ipa import inspect_ipa


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def smoke(ipa, bundle_id, private, output, exercise_missing_group=False):
    inspect_ipa(ipa, 'simulator', bundle_id)
    stage = private / 'simulator-app'
    stage.mkdir(parents=True, exist_ok=True)
    run('ditto', '-x', '-k', str(ipa), str(stage))
    apps = list((stage / 'Payload').glob('*.app'))
    if len(apps) != 1:
        raise ValueError('Expected one simulator app')
    runtimes = json.loads(run('xcrun', 'simctl', 'list', 'runtimes', '-j'))['runtimes']
    minimum = plistlib.loads((apps[0] / 'Info.plist').read_bytes()).get('MinimumOSVersion', '15.0')
    def version(value):
        return tuple(int(p) for p in value.split('.'))
    runtimes = [r for r in runtimes if r.get('isAvailable') and '.iOS-' in r['identifier']
                and version(r['version']) >= version(minimum)]
    if not runtimes:
        raise ValueError('No available compatible iOS simulator runtime')
    runtime = max(runtimes, key=lambda r: version(r['version']))
    device = run('xcrun', 'simctl', 'create', 'Asteri CI',
                 'com.apple.CoreSimulator.SimDeviceType.iPhone-17', runtime['identifier'])
    recorder = None
    record_log = None
    try:
        run('xcrun', 'simctl', 'boot', device)
        run('xcrun', 'simctl', 'bootstatus', device, '-b')
        run('xcrun', 'simctl', 'install', device, str(apps[0]))
        record_log = (output / 'simulator-recording.log').open('w')
        recorder = subprocess.Popen(['xcrun', 'simctl', 'io', device, 'recordVideo',
                                     '--codec=h264', '--force', str(output / 'simulator-launch.mp4')],
                                    stdout=record_log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 15
        while 'Recording started' not in (output / 'simulator-recording.log').read_text():
            if recorder.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('Simulator recording failed to start')
            time.sleep(0.1)
        launch = run('xcrun', 'simctl', 'launch', device, bundle_id)
        time.sleep(6)
        processes = run('xcrun', 'simctl', 'spawn', device, 'launchctl', 'list')
        if bundle_id not in processes:
            raise ValueError('App process exited after simulator launch')
        # The upstream app stops initialization with "Error 2" if its group container
        # cannot be resolved. Merely surviving as a process must not count as launch.
        info = plistlib.loads((apps[0] / 'Info.plist').read_bytes())
        if info.get('AsteriPrivateContainer') is True:
            if list((apps[0] / 'PlugIns').glob('*.appex')):
                raise ValueError('Standalone simulator build unexpectedly has app extensions')
            from pathlib import Path
            data = Path(run('xcrun', 'simctl', 'get_app_container', device, bundle_id, 'data'))
            if not (data / 'Library/Application Support/Asteri').is_dir():
                raise ValueError('Standalone app did not initialize its private data directory')
        else:
            run('xcrun', 'simctl', 'get_app_container', device, bundle_id, 'group.' + bundle_id)
        run('xcrun', 'simctl', 'io', device, 'screenshot', str(output / 'simulator-launch.png'))
        (output / 'simulator-smoke.json').write_text(json.dumps({
            'launch': launch, 'runtime': runtime['identifier'], 'device': device,
            'survived_seconds': 6, 'login_tested': False, 'device_tested': False,
            'private_container': info.get('AsteriPrivateContainer') is True,
        }, indent=2) + '\n', encoding='utf-8')
        if exercise_missing_group:
            recorder.send_signal(signal.SIGINT)
            recorder.wait(timeout=20)
            recorder = None
            record_log.close()
            record_log = None
            missing_group_scenario(apps[0], device, bundle_id, private, output)
    finally:
        if recorder is not None:
            recorder.send_signal(signal.SIGINT)
            recorder.wait(timeout=20)
        if record_log is not None:
            record_log.close()
        subprocess.run(['xcrun', 'simctl', 'io', device, 'screenshot',
                        str(output / 'simulator-last-frame.png')], check=False)
        logs = subprocess.run(['xcrun', 'simctl', 'spawn', device, 'log', 'show',
                               '--last', '2m', '--style', 'compact', '--predicate',
                               'process == "Telegram"'], capture_output=True, text=True)
        (output / 'simulator-system.log').write_text(logs.stdout + logs.stderr, encoding='utf-8')
        subprocess.run(['xcrun', 'simctl', 'shutdown', device], check=False)
        subprocess.run(['xcrun', 'simctl', 'delete', device], check=False)


def missing_group_scenario(app, device, bundle_id, private, output):
    """Fault injection into a staged simulator app, never into a delivery IPA.

    A standalone signature supplies no App Groups. Switching only its plist flag
    to shared mode exercises the shipping error page when the container is absent.
    """
    result = subprocess.run(['codesign', '-d', '--entitlements', ':-', str(app)],
                            capture_output=True, check=True)
    entitlements = plistlib.loads(result.stdout)
    if entitlements.get('com.apple.security.application-groups') or entitlements.get('aps-environment'):
        raise ValueError('Standalone signature unexpectedly requests App Groups or APNs')
    scope = entitlements.get('keychain-access-groups', [])
    if not scope or any(not group.endswith('.' + bundle_id) for group in scope):
        raise ValueError('Standalone signature must use only its own keychain group')
    (output / 'standalone-entitlements.plist').write_bytes(plistlib.dumps(entitlements))
    subprocess.run(['xcrun', 'simctl', 'terminate', device, bundle_id], check=False)
    # This simulator was created for this test and contains no signed-in account.
    run('xcrun', 'simctl', 'uninstall', device, bundle_id)
    info_path = app / 'Info.plist'
    info = plistlib.loads(info_path.read_bytes())
    if info.get('AsteriPrivateContainer') is not True:
        raise ValueError('Missing-group exercise requires a compiled standalone app')
    info['AsteriPrivateContainer'] = False
    info_path.write_bytes(plistlib.dumps(info))
    entitlement_path = private / 'simulator-test-entitlements.plist'
    entitlement_path.write_bytes(plistlib.dumps(entitlements))
    run('codesign', '--force', '--sign', '-', '--entitlements', str(entitlement_path),
        '--generate-entitlement-der', str(app))
    run('codesign', '--verify', '--strict', str(app))
    run('xcrun', 'simctl', 'install', device, str(app))
    recorder = None
    with (output / 'missing-group-recording.log').open('w') as log:
        try:
            recorder = subprocess.Popen(['xcrun', 'simctl', 'io', device, 'recordVideo',
                                         '--codec=h264', '--force', str(output / 'missing-group.mp4')],
                                        stdout=log, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 15
            while 'Recording started' not in (output / 'missing-group-recording.log').read_text():
                if recorder.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('Missing-group video recording failed to start')
                time.sleep(0.1)
            run('xcrun', 'simctl', 'launch', device, bundle_id)
            time.sleep(5)
            check = subprocess.run(['xcrun', 'simctl', 'get_app_container', device, bundle_id,
                                    'group.' + bundle_id], capture_output=True, text=True)
            if check.returncode == 0:
                raise ValueError('Expected an unavailable shared container in the injected failure case')
            run('xcrun', 'simctl', 'io', device, 'screenshot', str(output / 'missing-group.png'))
        finally:
            if recorder is not None:
                recorder.send_signal(signal.SIGINT)
                recorder.wait(timeout=20)
    (output / 'missing-group-scenario.json').write_text(json.dumps({
        'shared_container_unavailable': True, 'staged_plist_modified_for_test': True,
        'delivery_ipa_modified': False, 'human_frame_inspection': 'pending',
    }, indent=2) + '\n')
