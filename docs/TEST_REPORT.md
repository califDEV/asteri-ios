# Test report

2026-11-25, Windows development host. No application/device success is implied.

| Check | Observed result |
|---|---|
| GitHub authentication | Owner `califDEV` authenticated; repository created |
| Secrets | `TELEGRAM_BUILD_CONFIGURATION` exists; value not read back |
| Local infrastructure unittest suite | 11 tests passed |
| Python source compilation | Passed using bundled CPython 3.12 |
| GitHub workflow static validation | Passed with actionlint 1.7.12; documented hosted preview label allowlisted |
| Required iOS submodule checkout | All 12 initialized at pinned revisions |
| Android reference working tree | Clean; required submodules initialized; optional upstream-disabled test262 excluded |
| Source publication | Full upstream history pushed to `https://github.com/califDEV/asteri-ios`; default branch `asteri/main` |
| Native ARM64 compilation | Actions enabled; initial workflow registration/dispatch under investigation |
| IPA structure / Mach-O | Inspector implemented and regression tested; no real app artifact inspected yet |
| Signed build / installation | Not run; Apple signing material not supplied |
| Simulator app / physical iPhone | Not run |
| Account, chat, send/receive, voice, media, restart | Not run |
| extera feature / existing plugin compatibility | Not run; no port implemented yet |
| Performance / visual animations | Not measured |

The inspector tests use temporary synthetic binary headers solely to exercise rejection
of wrong architecture/platform, malformed files, unsafe paths and wrong identities.
Those fixtures are not compiled applications and are never uploaded as IPA artifacts.
Provisioning tests cover expiry, team mismatch, wildcard keychain groups, foreign groups
and unexpected capabilities. Real codesign verification still requires macOS and profiles.

After first successful compilation, record the exact commit, run URL, IPA SHA-256 and
inspection report before tagging a baseline. Physical-device claims need actual evidence.
