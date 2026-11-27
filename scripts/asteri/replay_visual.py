#!/usr/bin/env python3
"""Record the already compiled, checksum-verified native settings harness."""
import json
import os
import platform
import subprocess

from build import ROOT, OUTPUT, write_json
from inspect_ipa import inspect_ipa
from visual import record_harness, run


def main():
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise ValueError('Requires an ARM64 macOS simulator runner')
    parent = str(int(os.environ['PARENT_RUN_ID']))
    version = json.loads((ROOT / 'versions.json').read_text())['xcode']
    subprocess.run(['sudo', 'xcode-select', '-s', '/Applications/Xcode_' + version + '.app/Contents/Developer'], check=True)
    source = ROOT / 'build-input/harness-replay'
    expected = json.loads((source / 'harness-inspection.json').read_text())
    provenance = json.loads((source / 'provenance.json').read_text())
    ipa = source / 'AsteriHarness.ipa'
    inspection = inspect_ipa(ipa, 'simulator', 'org.asteri.VisualHarness', 'asteri-harness')
    if inspection['sha256'] != expected['sha256']:
        raise ValueError('The retained harness differs from its compiler-output inspection')
    if provenance['run_url'].rstrip('/').split('/')[-1] != parent:
        raise ValueError('Harness provenance does not match the requested parent run')
    write_json(OUTPUT / 'replay-provenance.json', {
        'parent_run': parent, 'app_source_commit': provenance['source_commit'],
        'test_source_commit': run('git', 'rev-parse', 'HEAD'), 'app_sha256': inspection['sha256'],
        'compiled_harness_reused_without_modification': True,
    })
    record_harness(ipa, provenance['source_commit'])


if __name__ == '__main__':
    main()
