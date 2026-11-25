# Source, attribution and branding notes

The original source histories/notices and third-party license files are preserved.
This is an inventory note, not a completed license clearance of every bundled component.

The Android reference's [LICENSE](https://github.com/exteraSquad/exteraGram/blob/b4d852f48f2734a0bee1a74a0939be621612262a/LICENSE)
states GPL version 3 or later. Its [ADDITIONAL_TERMS.md](https://github.com/exteraSquad/exteraGram/blob/b4d852f48f2734a0bee1a74a0939be621612262a/ADDITIONAL_TERMS.md)
requires attribution/linkage for covered derived material, identification of modified
versions, and excludes trademark permission for the exteraGram name/icons as modified-app
identity. Covered source file notices must remain when code is ported. This is why the
application working name is Asteri and original exteraGram icons have not been copied.

The pinned Telegram-iOS root has no single LICENSE file; it retains notices and licenses
through its source and bundled dependencies. Do not invent a blanket replacement license.
Before distribution, complete a component/source-notice audit, retain the required
license texts and correspondence of source to binaries, and resolve any incompatible
component terms. Existing LICENSE/COPYING files in third-party modules are not removed.

Telegram's [API onboarding requirements](https://core.telegram.org/api/obtaining_api_id)
and [API terms](https://core.telegram.org/api/terms) apply to the client. Build configuration
uses the owner's own API ID/hash in GitHub Secrets. The upstream example configuration is
preserved as source history and is not used by the port's CI.

Before a final release: integrate an independent app icon/name and an About notice linking
to exteraGram and Telegram-iOS; finish resource/font/icon-pack attribution checks; include
licenses for any Python runtime and native extensions actually vendored; publish matching
source. The baseline artifact is development evidence and is not the completed branded port.
