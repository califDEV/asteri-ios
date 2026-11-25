import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import validate_config


def valid_config():
    return dict(bundle_id='org.example.asteri', api_id='123456', api_hash='a' * 32,
                team_id='UNSIGNED00', is_internal_build='true', is_appstore_build='false',
                appstore_id='0', app_specific_url_scheme='asteri', premium_iap_product_id='',
                enable_siri=False, enable_icloud=False)


class ConfigurationTests(unittest.TestCase):
    def test_valid_unsigned(self):
        self.assertEqual(validate_config(json.dumps(valid_config()), 'unsigned'), valid_config())

    def test_reject_missing_invalid_and_official_configuration(self):
        for raw in ('', '[]', '{', 'null'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                validate_config(raw, 'unsigned')
        for key, value in (('api_id', '8'), ('api_hash', 'invalid'), ('team_id', ''),
                           ('bundle_id', 'ph.telegra.Telegraph'), ('enable_siri', 'False'),
                           ('bundle_id', 'org.example"\nmalicious = True')):
            config = valid_config()
            config[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_config(json.dumps(config), 'unsigned')

    def test_signed_requires_real_team(self):
        with self.assertRaises(ValueError):
            validate_config(json.dumps(valid_config()), 'signed')
