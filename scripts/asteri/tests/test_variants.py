import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import configuration


class StorageVariantTests(unittest.TestCase):
    def config(self):
        return json.dumps(dict(bundle_id='org.example.asteri', api_id='12345', api_hash='a' * 32,
                               team_id='UNSIGNED00', is_internal_build='true', is_appstore_build='false',
                               appstore_id='0', app_specific_url_scheme='asteri', premium_iap_product_id='',
                               enable_siri=False, enable_icloud=False))

    def test_explicit_standalone_mode_has_separate_identity(self):
        with patch.dict(os.environ, TELEGRAM_BUILD_CONFIGURATION=self.config(), BUILD_MODE='unsigned', PRIVATE_CONTAINER='true'):
            value = configuration()
            self.assertEqual(value['bundle_id'], 'org.example.asteri.sideload')
            self.assertEqual(value['app_specific_url_scheme'], 'asteri-sideload')
        with patch.dict(os.environ, TELEGRAM_BUILD_CONFIGURATION=self.config(), BUILD_MODE='unsigned', PRIVATE_CONTAINER='false'):
            self.assertEqual(configuration()['bundle_id'], 'org.example.asteri')

    def test_invalid_mode_is_rejected_instead_of_switching_storage(self):
        with patch.dict(os.environ, TELEGRAM_BUILD_CONFIGURATION=self.config(), BUILD_MODE='unsigned', PRIVATE_CONTAINER='yes'):
            with self.assertRaises(ValueError):
                configuration()
