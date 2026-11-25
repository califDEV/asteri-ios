"""Login-free launch smoke test. Does not assert Telegram account functionality."""
import json
import plistlib
import subprocess
import time
from inspect_ipa import inspect_ipa


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def smoke(ipa, bundle_id, private, output):
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
    try:
        run('xcrun', 'simctl', 'boot', device)
        run('xcrun', 'simctl', 'bootstatus', device, '-b')
        run('xcrun', 'simctl', 'install', device, str(apps[0]))
        launch = run('xcrun', 'simctl', 'launch', device, bundle_id)
        time.sleep(6)
        processes = run('xcrun', 'simctl', 'spawn', device, 'launchctl', 'list')
        if bundle_id not in processes:
            raise ValueError('App process exited after simulator launch')
        # The upstream app stops initialization with "Error 2" if its group container
        # cannot be resolved. Merely surviving as a process must not count as launch.
        run('xcrun', 'simctl', 'get_app_container', device, bundle_id, 'group.' + bundle_id)
        run('xcrun', 'simctl', 'io', device, 'screenshot', str(output / 'simulator-launch.png'))
        (output / 'simulator-smoke.json').write_text(json.dumps({
            'launch': launch, 'runtime': runtime['identifier'], 'device': device,
            'survived_seconds': 6, 'login_tested': False, 'device_tested': False,
        }, indent=2) + '\n', encoding='utf-8')
    finally:
        logs = subprocess.run(['xcrun', 'simctl', 'spawn', device, 'log', 'show',
                               '--last', '2m', '--style', 'compact', '--predicate',
                               'process == "Telegram"'], capture_output=True, text=True)
        (output / 'simulator-system.log').write_text(logs.stdout + logs.stderr, encoding='utf-8')
        subprocess.run(['xcrun', 'simctl', 'shutdown', device], check=False)
        subprocess.run(['xcrun', 'simctl', 'delete', device], check=False)
