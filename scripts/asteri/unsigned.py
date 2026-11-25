"""Explicit unsigned archive support for the pinned local rules_apple checkout.

Signed builds retain the original mandatory-profile path. No certificate/profile is
fabricated, and the device target/SDK/architecture are unchanged.
"""
import hashlib

SOURCE_SHA256 = 'b6776b1c10a2c965f01259dd95ebe1b045afc5e22b3446b8ae81d44f11c3a7da'
OLD = ('if platform_prerequisites.platform.is_device:\n'
       '        processor_partials.append(\n'
       '            partials.provisioning_profile_partial(')
CONDITION = ('platform_prerequisites.platform.is_device and not '
             '("asteri.unsigned_archive" in features and "disable_legacy_signing" in features)')
NEW = 'if ' + CONDITION + ':\n' + OLD.split('\n', 1)[1]


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def transform(text, expected_digest=SOURCE_SHA256, expected_sites=6):
    original = text.replace(NEW, OLD)
    if digest(original) != expected_digest or original.count(OLD) != expected_sites:
        raise ValueError('rules_apple source differs from the audited pin; review the unsigned archive patch')
    if NEW in text and text.count(NEW) != expected_sites:
        raise ValueError('Partial unsigned archive patch detected')
    return original.replace(OLD, NEW)


def apply(path):
    source = path.read_text(encoding='utf-8')
    patched = transform(source)
    path.write_text(patched, encoding='utf-8', newline='\n')
    return {'source_sha256': SOURCE_SHA256, 'patched_sha256': digest(patched),
            'profile_embedding_sites': 6,
            'required_features': ['asteri.unsigned_archive', 'disable_legacy_signing']}


def restore(path):
    if not path.is_file():
        return
    text = path.read_text(encoding='utf-8')
    if NEW not in text:
        return
    transform(text)  # Reject unrelated edits instead of overwriting them.
    path.write_text(text.replace(NEW, OLD), encoding='utf-8', newline='\n')
