import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unsigned import OLD, NEW, transform, digest


class UnsignedArchiveTests(unittest.TestCase):
    def test_signed_and_single_flag_builds_still_embed_and_require_profiles(self):
        # Evaluate the exact condition inserted in the Starlark rule, not a second
        # Python implementation of its policy. This expression is shared syntax.
        condition = NEW.split('\n')[0][3:-1]
        expression = compile(ast.parse(condition, mode='eval'), '<profile gate>', 'eval')
        device = SimpleNamespace(platform=SimpleNamespace(is_device=True))
        for features in ([], ['asteri.unsigned_archive'], ['disable_legacy_signing']):
            self.assertTrue(eval(expression, {'platform_prerequisites': device, 'features': features}))
        self.assertFalse(eval(expression, {'platform_prerequisites': device,
                                         'features': ['asteri.unsigned_archive', 'disable_legacy_signing']}))

    def test_source_pin_rejects_unreviewed_or_partial_changes(self):
        original = OLD + ')\n'
        with self.assertRaises(ValueError):
            transform(original)  # The fixture is not the audited vendored source.
        changed = transform(original, digest(original), 1)
        self.assertEqual(transform(changed, digest(original), 1), changed)
        with self.assertRaises(ValueError):
            transform(original + 'unreviewed change', digest(original), 1)
        with self.assertRaises(ValueError):
            transform(changed + original, digest(original + original), 2)
