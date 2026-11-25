# Patches to external repositories

`MODULE.bazel` applies the patches in this directory.

## Asteri unsigned device archives

`scripts/asteri/unsigned.py` also applies the reviewable
`asteri-unsigned-provisioning.patch` to the **local submodule override** only for
unsigned device archives, after verifying its source SHA-256. Because this repository
uses `local_path_override`, MODULE.bazel does not apply that patch itself. Cleanup
restores the exact original rule. Two explicit features are required to omit embedded
profiles: `asteri.unsigned_archive` and `disable_legacy_signing`. Normal/signed builds
retain the original mandatory profile check; no fake profiles are generated. Simulator
platform selection is unaffected. Review the patch and source hash together on upstream bumps.

## `xctestrunner-collect-test-diagnostics.patch`

rules_apple's `ios_test_runner` drives xcodebuild through xctestrunner, which passes `-collect-test-diagnostics=never`.
xcodebuild reads that `=` spelling as a build setting and silently ignores it (`-collect-test-diagnostics=bogus` is
accepted; `-collect-test-diagnostics bogus` is rejected), so diagnostics stay `on-failure` and every failing run ends in
`simctl diagnose -l -b --timeout=600 …`, which can hold the run for up to 10 minutes after its last test (and the
timeout stops while the Mac sleeps). The patch passes the flag and its value as two arguments. An xctestrunner bump that
no longer matches the patch fails the build rather than quietly bringing the stall back.

**If a failing run still stalls after its `Test Suite … failed` line:** `pgrep -fl "simctl diagnose"`. A hit means the
patch is not in effect; killing that process is safe (it only collects logs) and the run returns at once with its real
result. Scripts that call xcodebuild themselves pass `-collect-test-diagnostics never`, as two arguments.
