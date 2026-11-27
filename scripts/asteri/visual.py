#!/usr/bin/env python3
"""Record shipping Asteri settings rows against an empty, real preference store."""
import json
import os
import plistlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from build import ROOT, OUTPUT, PRIVATE, preflight, prepare, logged, write_json
from inspect_ipa import inspect_ipa
from simulator import create_simulator


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def wait_for_state(path, predicate):
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        try:
            value = json.loads(path.read_text())
            if value.get('error'):
                raise RuntimeError(value['error'])
            if predicate(value):
                return value
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        time.sleep(0.2)
    raise RuntimeError('Harness did not reach the required preference state')


def main():
    if os.getenv('BUILD_MODE') != 'simulator':
        raise ValueError('The visual harness must use simulator mode')
    for executable in ('ffmpeg', 'ffprobe'):
        if not shutil.which(executable):
            raise ValueError(f'{executable} is required for timestamped recorded-frame verification')
    preflight()
    config, config_path = prepare()
    command = [sys.executable, '-u', 'build-system/Make/Make.py', 'build',
               '--configurationPath', str(config_path), '--buildNumber', '1',
               '--configuration', 'debug_sim_arm64', '--xcodeManagedCodesigning',
               '--target', '//Tests/AsteriHarness:AsteriHarness']
    metadata_command = command[:-1] + ['//Tests/AsteriHarness:InfoPlist']
    logged(metadata_command, 'visual-metadata.log', (config['api_hash'],))
    metadata = plistlib.loads((ROOT / 'bazel-bin/Tests/AsteriHarness/InfoPlist.plist').read_bytes())
    if metadata.get('CFBundlePackageType') != 'APPL':
        raise ValueError('Harness metadata must identify a real application before compilation')
    ipa = ROOT / 'bazel-bin/Tests/AsteriHarness/AsteriHarness.ipa'
    retained_ipa = OUTPUT / 'AsteriHarness.ipa'
    try:
        logged(command, 'visual-build.log', (config['api_hash'],))
    finally:
        if ipa.is_file():
            shutil.copy2(ipa, retained_ipa)
    record_harness(retained_ipa, run('git', 'rev-parse', 'HEAD'))


def record_harness(ipa, app_source):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    inspection = inspect_ipa(ipa, 'simulator', 'org.asteri.VisualHarness', 'asteri-harness')
    write_json(OUTPUT / 'harness-inspection.json', inspection)
    device, runtime, device_type = create_simulator('Asteri-QA-' + os.getenv('GITHUB_RUN_ID', 'local'), ('iPhone 18 Pro', 'iPhone 17 Pro', 'iPhone 17'))
    recorder = None
    record_log = None
    bundle = 'org.asteri.VisualHarness'
    try:
        run('xcrun', 'simctl', 'boot', device)
        run('xcrun', 'simctl', 'bootstatus', device, '-b')
        run('xcrun', 'simctl', 'status_bar', device, 'override', '--time', '9:41',
            '--batteryState', 'charged', '--batteryLevel', '100')
        with tempfile.TemporaryDirectory(dir=PRIVATE) as temp:
            with zipfile.ZipFile(ipa) as archive:
                archive.extractall(temp)  # inspect_ipa already rejected unsafe entries.
            apps = list((Path(temp) / 'Payload').glob('*.app'))
            if len(apps) != 1:
                raise ValueError('Harness does not contain a single app')
            run('xcrun', 'simctl', 'install', device, str(apps[0]))
        run('xcrun', 'simctl', 'launch', device, bundle)
        container = Path(run('xcrun', 'simctl', 'get_app_container', device, bundle, 'data'))
        state_path = container / 'Documents/state.json'
        states = [wait_for_state(state_path, lambda s: s['filterZalgo'] is True)]
        record_log = (OUTPUT / 'recording.log').open('w')
        recorder = subprocess.Popen(['xcrun', 'simctl', 'io', device, 'recordVideo',
                                     '--codec=h264', '--force', str(OUTPUT / 'settings.mp4')],
                                    stdout=record_log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 15
        while 'Recording started' not in (OUTPUT / 'recording.log').read_text():
            if recorder.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('Simulator video recording did not start')
            time.sleep(0.1)

        def snapshot(name):
            time.sleep(0.8)
            run('xcrun', 'simctl', 'io', device, 'screenshot', str(OUTPUT / (name + '.png')))

        snapshot('01-enabled-light')
        run('xcrun', 'simctl', 'openurl', device, 'asteri-harness://toggle')
        states.append(wait_for_state(state_path, lambda s: s['filterZalgo'] is False and s['lastAction'] == 'toggle'))
        snapshot('02-disabled-light')
        token = states[-1]['launchToken']
        run('xcrun', 'simctl', 'terminate', device, bundle)
        run('xcrun', 'simctl', 'launch', device, bundle)
        states.append(wait_for_state(state_path, lambda s: s['launchToken'] != token and s['filterZalgo'] is False))
        snapshot('03-disabled-after-restart')
        run('xcrun', 'simctl', 'openurl', device, 'asteri-harness://toggle')
        states.append(wait_for_state(state_path, lambda s: s['filterZalgo'] is True and s['lastAction'] == 'toggle'))
        snapshot('04-enabled-again')
        run('xcrun', 'simctl', 'openurl', device, 'asteri-harness://dark')
        states.append(wait_for_state(state_path, lambda s: s['lastAction'] == 'dark' and s['filterZalgo'] is True))
        snapshot('05-enabled-dark')
        run('xcrun', 'simctl', 'openurl', device, 'asteri-harness://light')
        states.append(wait_for_state(state_path, lambda s: s['lastAction'] == 'light' and s['filterZalgo'] is True))
        snapshot('06-light-restored')
        recorder.send_signal(signal.SIGINT)
        recorder.wait(timeout=20)
        recorder = None
        record_log.close()
        record_log = None
        frames = OUTPUT / 'frames'
        frames.mkdir(exist_ok=True)
        timestamps = run('ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames',
                         '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json',
                         str(OUTPUT / 'settings.mp4'))
        (OUTPUT / 'frame-timestamps.json').write_text(timestamps + '\n')
        run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(OUTPUT / 'settings.mp4'),
            '-vsync', '0', str(frames / '%05d.png'))
        count = len(list(frames.glob('*.png')))
        if count != len(json.loads(timestamps)['frames']) or count < 2:
            raise ValueError('Extracted frames do not match original ffprobe timestamps')
        write_json(OUTPUT / 'visual-scenarios.json', {
            'states': states, 'frames': count, 'runtime': runtime, 'device_type': device_type,
            'source_commit': app_source, 'test_source_commit': run('git', 'rev-parse', 'HEAD'), 'recorded': True,
            'human_frame_inspection': 'pending', 'real_chat_tested': False, 'device_tested': False,
        })
        print(f'Recorded {count} original video frames; inspect before claiming visual success.')
    finally:
        if recorder is not None:
            recorder.send_signal(signal.SIGINT)
            recorder.wait(timeout=20)
        if record_log is not None:
            record_log.close()
        log = subprocess.run(['xcrun', 'simctl', 'spawn', device, 'log', 'show', '--last', '2m',
                              '--style', 'compact', '--predicate', 'process == "AsteriHarness"'],
                             capture_output=True, text=True)
        (OUTPUT / 'simulator-system.log').write_text(log.stdout + log.stderr)
        subprocess.run(['xcrun', 'simctl', 'shutdown', device], check=False)
        subprocess.run(['xcrun', 'simctl', 'delete', device], check=False)


if __name__ == '__main__':
    main()
