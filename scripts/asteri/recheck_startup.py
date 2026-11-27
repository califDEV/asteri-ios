#!/usr/bin/env python3
"""Replay launch tests on the immutable compiled simulator IPA; no compilation."""
import json
import os
import platform
import subprocess
from pathlib import Path

from build import ROOT, OUTPUT, PRIVATE, write_json
from inspect_ipa import inspect_ipa
from simulator import smoke, run


def main():
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise ValueError('Requires the ARM64 macOS simulator runner')
    parent_run = str(int(os.environ['PARENT_RUN_ID']))
    versions = json.loads((ROOT / 'versions.json').read_text())
    developer = '/Applications/Xcode_' + versions['xcode'] + '.app/Contents/Developer'
    subprocess.run(['sudo', 'xcode-select', '-s', developer], check=True)
    source = ROOT / 'build-input/recheck-artifacts'
    original = json.loads((source / 'ipa-inspection.json').read_text())
    provenance = json.loads((source / 'provenance.json').read_text())
    ipa = source / 'Asteri.ipa'
    inspection = inspect_ipa(ipa, 'simulator', original['bundle_id'], 'asteri-sideload')
    checksum = (source / 'SHA256SUMS').read_text().split()
    if inspection['sha256'] != original['sha256'] or checksum != [inspection['sha256'], 'Asteri.ipa']:
        raise ValueError('Parent IPA checksum does not match its published inspection')
    if not inspection['private_container']:
        raise ValueError('Startup replay requires the explicit standalone variant')
    if provenance['run_url'].rstrip('/').split('/')[-1] != parent_run:
        raise ValueError('Parent provenance does not match the requested run')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT / 'recheck-provenance.json', {
        'parent_run': parent_run, 'app_source_commit': provenance['source_commit'],
        'test_source_commit': run('git', 'rev-parse', 'HEAD'), 'app_sha256': inspection['sha256'],
        'compiled_app_reused_without_modification': True,
    })
    smoke(ipa, inspection['bundle_id'], PRIVATE, OUTPUT, exercise_missing_group=True)
    for stem in ('simulator-launch', 'missing-group'):
        frame_dir = OUTPUT / (stem + '-frames')
        frame_dir.mkdir(exist_ok=True)
        timestamps = run('ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames',
                         '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json',
                         str(OUTPUT / (stem + '.mp4')))
        (OUTPUT / (stem + '-timestamps.json')).write_text(timestamps + '\n')
        run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(OUTPUT / (stem + '.mp4')),
            '-vsync', '0', str(frame_dir / '%05d.png'))
        if len(list(frame_dir.glob('*.png'))) != len(json.loads(timestamps)['frames']):
            raise ValueError('Frame count differs from original ffprobe timestamps')


if __name__ == '__main__':
    main()
