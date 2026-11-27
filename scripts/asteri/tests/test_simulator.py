import json
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simulator import create_simulator


class SimulatorCompatibilityTests(unittest.TestCase):
    def inventories(self):
        return [json.dumps({'runtimes': [
            dict(isAvailable=True, version='27.2', identifier='com.apple.CoreSimulator.SimRuntime.iOS-27-2-iPhone19-4'),
            dict(isAvailable=True, version='27.0', identifier='com.apple.CoreSimulator.SimRuntime.iOS-27-0'),
        ]}), json.dumps({'devicetypes': [dict(name='iPhone 17', identifier='type.iphone17')]})]

    def test_newest_device_specific_runtime_does_not_prevent_compatible_launch(self):
        def create(arguments, **kwargs):
            if arguments[-1].endswith('iPhone19-4'):
                return SimpleNamespace(returncode=147, stdout='', stderr='Incompatible device type')
            return SimpleNamespace(returncode=0, stdout='dedicated-test-device\n', stderr='')
        with patch('simulator.run', side_effect=self.inventories()), patch('simulator.subprocess.run', side_effect=create):
            device, runtime, kind = create_simulator('test')
        self.assertEqual(device, 'dedicated-test-device')
        self.assertEqual(runtime['version'], '27.0')
        self.assertEqual(kind['identifier'], 'type.iphone17')

    def test_no_compatible_pair_reports_the_native_failure(self):
        with patch('simulator.run', side_effect=self.inventories()), patch('simulator.subprocess.run', return_value=SimpleNamespace(returncode=147, stdout='', stderr='Incompatible device type')):
            with self.assertRaisesRegex(RuntimeError, 'Incompatible device type'):
                create_simulator('test')
