# Build guide

Work in progress, checked against pinned sources on 2026-11-25. No local Mac is required.
The source pin's `versions.json` requires Xcode 27.1, Bazel 9.2.0 and macOS 27.
The standard [xcode-27 runner image](https://github.com/actions/runner-images/blob/main/images/macos/xcode-27-arm64-Readme.md)
lists Xcode 27.1. The workflow checks the installed version at runtime and fails on a mismatch.
The official `BazelLocation.py` downloads Bazel and verifies the SHA-256 in `versions.json`.

1. Obtain your own Telegram API ID and API Hash at [my.telegram.org/apps](https://my.telegram.org/apps).
2. Run `scripts/asteri/Set-BuildSecrets.ps1` in PowerShell. If local script execution is
   disabled, run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <absolute-script-path>`.
   This exception applies only to that process. It writes the private JSON directly to
   GitHub Actions secret `TELEGRAM_BUILD_CONFIGURATION`, without a local credentials file.
3. Dispatch `ios-build.yml` on `asteri/main` with `mode=unsigned`. The workflow uses the
   official `build-system/Make/Make.py build --configuration=release_arm64`.
4. Download the `asteri-unsigned-<run-id>` artifact only after the job succeeds. It contains
   `Asteri.ipa`, `SHA256SUMS`, `ipa-inspection.json`, provenance and build logs.

For the standalone Sideloadly variant, also set `private_container=true`. It builds a
separate `.sideload` bundle with its own `asteri-sideload` URL scheme and private app
storage, without extensions, App Groups or APNs capabilities. This is an explicit build
variant; it never silently switches an existing shared account database to a new folder.
The application's own validated keychain group still protects credentials; passcode,
biometric and encryption policies remain active. Physical installation must be tested
with the owner's signing. See `features/sideload-storage.md` for its current evidence.

Unsigned mode uses no certificate or provisioning profile. The explicit `UNSIGNED00`
Team ID is a configuration sentinel, not a signing credential. Generated Bazel flags
disable provisioning profiles and legacy signing using mechanisms present in the pinned
sources. The generated RC file is isolated under `build-input/`; upstream Make.py is retained.
ARM64 simulator binaries are rejected as device artifacts by inspecting `LC_BUILD_VERSION`.

The first real build showed that rules_apple also unconditionally embeds profiles for
device apps/extensions. Unsigned mode now applies a SHA-256-checked, reviewable patch
(`build-system/bazel-patches/asteri-unsigned-provisioning.patch`) to that local submodule.
Only the combination `asteri.unsigned_archive` + `disable_legacy_signing` omits profile
embedding; normal/signed builds retain the original checks. App/extensions remain real
ARM64 device targets. Cleanup restores the exact source; the applied digests are retained
in `unsigned-rules-patch.json`. No fabricated provisioning material is used.

Signed mode requires a real Team ID in the JSON secret, `IOS_SIGNING_ARCHIVE_BASE64`
(base64 ZIP containing `certs/*.p12` and `profiles/*.mobileprovision`) and
`IOS_CERTIFICATE_PASSWORD`. Supply profiles for every enabled extension, matching bundle IDs,
App Groups, keychain groups, and capabilities. The existing upstream resolver requires an
APS environment in provisioning material. Certificate import uses an ephemeral keychain.
This path is implemented but requires real signing material for validation.

`mode=simulator` builds `debug_sim_arm64`, runs native UrlWhitelist regression tests,
installs and launches the app without login, records a screenshot and system logs.
It does not establish account/messaging functionality. It chooses an available compatible
iOS runtime instead of assuming the upstream tests' iOS 26.5 simulator exists on this image.
Simulator builds retain normal local ad-hoc signing so their declared entitlements survive
installation. `ios-startup.yml` can replay a verified compiled standalone simulator IPA,
check that its signature requests no App Groups/APNs, and record the normal launch plus
an explicitly injected missing-group failure. The delivery IPA is never changed by this
fault-injection test; only a staging copy inside a fresh simulator is changed/re-signed.

Builds are manual to limit runner use. The public repository uses standard runners; no
paid runner or VM service is selected. Repository download archives are cached; private
configuration, certificates, Bazel output trees and Telegram sessions are never cached.
The runner's actual free space is recorded; a cold full build may exceed its resources.
Logs and artifacts expire after 7 days. Releases require an existing tag on the workflow
commit, a successful build, and a checksum verification. Do not publish the baseline as
a completed port: independent branding and device testing remain pending.

Install only a final tested build. An unsigned IPA cannot launch directly on iPhone: it
must first be signed for that device by a compatible sideloading tool. Free provisioning
may not support the entitlements/app groups/extensions required by the full client.
`disable_extensions=true` makes a limited variant and must be recorded as such; it does
not guarantee free-account compatibility. Installation, push notifications and app-group
storage remain unverified until tested with real credentials on the target iPhone.
