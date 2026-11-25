import datetime
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from signing import verify_profile


class ProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.entitlements = {'application-identifier': 'ABCDEFGHIJ.org.example.asteri',
                             'com.apple.developer.team-identifier': 'ABCDEFGHIJ',
                             'keychain-access-groups': ['ABCDEFGHIJ.org.example.asteri'],
                             'get-task-allow': False}
        self.profile = {'ExpirationDate': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
                        'TeamIdentifier': ['ABCDEFGHIJ'], 'Entitlements': dict(self.entitlements)}
        self.profile['Entitlements']['keychain-access-groups'] = ['ABCDEFGHIJ.*']

    def test_matching_profile_and_wildcard_groups(self):
        verify_profile(self.profile, self.entitlements, 'ABCDEFGHIJ', 'org.example.asteri')

    def test_reject_expiry_and_team_mismatch(self):
        with self.assertRaises(ValueError):
            verify_profile(self.profile, self.entitlements, 'WRONGTEAM0', 'org.example.asteri')
        self.profile['ExpirationDate'] -= datetime.timedelta(days=2)
        with self.assertRaises(ValueError):
            verify_profile(self.profile, self.entitlements, 'ABCDEFGHIJ', 'org.example.asteri')

    def test_reject_extra_and_unpermitted_capabilities(self):
        self.entitlements['com.apple.security.application-groups'] = ['group.foreign']
        with self.assertRaises(ValueError):
            verify_profile(self.profile, self.entitlements, 'ABCDEFGHIJ', 'org.example.asteri')
        del self.entitlements['com.apple.security.application-groups']
        self.entitlements['keychain-access-groups'] = ['FOREIGN000.session']
        with self.assertRaises(ValueError):
            verify_profile(self.profile, self.entitlements, 'ABCDEFGHIJ', 'org.example.asteri')
