# Test report

Checks from 2026-11-25–26, Windows development host and GitHub macOS runners.
Device behavior remains untested; the real device-targeted application compiled successfully.

On 2026-11-26, [run 45715952913](https://github.com/califDEV/asteri-ios/actions/runs/45715952913)
completed successfully from `c282490f0dd2e804f9fe91e8aed9669a3d46e07c`.
Official Make.py produced a real 80,671,077-byte unsigned IPA (13.2, build 4, iOS 15.0+),
including the main ARM64 iPhoneOS executable, five frameworks and six extensions.
All twelve Mach-O executables passed device-platform and type inspection; main bundle
`org.asteri.califdev` and configured `asteri` URL scheme matched. The downloaded file
was inspected again on Windows and its SHA-256 matched the runner's report:
`1b3e71d88ca81dc9e420672223f24b7a2c13263e50c6aeb3136aec8dba3f1700`.
Baseline tag: `baseline-ios-13.2-20261126`. Machine-readable evidence is in
`docs/builds/baseline-ios-13.2-20261126/`. No signing, launch or account test is implied.

| Check | Observed result |
|---|---|
| GitHub authentication | Owner `califDEV` authenticated; repository created |
| Secrets | `TELEGRAM_BUILD_CONFIGURATION` exists; value not read back |
| Local infrastructure unittest suite | 13 tests passed, including signed/unsigned profile-gating regression checks (2026-11-26) |
| GitHub infrastructure suite | [Successful run 45708384597](https://github.com/califDEV/asteri-ios/actions/runs/45708384597), 11 tests and Python compilation; source `f87393a6cbc6020d4c93a2b6fc6e10c4d9e18b9e` |
| Updated GitHub infrastructure suite | [45709608632](https://github.com/califDEV/asteri-ios/actions/runs/45709608632) passed 13 tests; also passed alongside native tests in [45711409372](https://github.com/califDEV/asteri-ios/actions/runs/45711409372) |
| Native Swift text prototype | [45711409372](https://github.com/califDEV/asteri-ios/actions/runs/45711409372): compiled on ARM64 macOS with Apple Swift 6.4; 10 XCTest cases passed. No app integration yet; source `88ed8ba542aff12287f060211e8a31216a791bd3` |
| Native text release/iOS SDK verification | [45712163625](https://github.com/califDEV/asteri-ios/actions/runs/45712163625): same 10 scenarios passed in debug and release; source compiled with the pinned Xcode's iPhoneOS SDK for `arm64-apple-ios15.0`. This emits a module, not an executable app or IPA; source `f72a7b4059ee4f07127acf0f4ca7d9cd843fe0d9` |
| Python source compilation | Passed using bundled CPython 3.12 |
| GitHub workflow static validation | Passed with actionlint 1.7.12; documented hosted preview label allowlisted |
| Required iOS submodule checkout | All 12 initialized at pinned revisions |
| Android reference working tree | Clean; required submodules initialized; optional upstream-disabled test262 excluded |
| Source publication | Full upstream history pushed to `https://github.com/califDEV/asteri-ios`; default branch `asteri/main` |
| Native ARM64 compilation | [First run 45708379459](https://github.com/califDEV/asteri-ios/actions/runs/45708379459) failed at rules_apple analysis: mandatory device provisioning for IntentsExtension, before compilation. Full log and artifacts retained locally. An explicit unsigned archive path is prepared for retry |
| IPA structure / Mach-O | Real IPA from 45715952913 inspected on runner and Windows; all twelve binaries target ARM64 iPhoneOS |
| Signed build / installation | Not run; Apple signing material not supplied |
| Simulator app / physical iPhone | Not run |
| Account, chat, send/receive, voice, media, restart | Not run |
| App-integrated extera feature / existing plugin compatibility | Not run; isolated Zalgo prototype is tested separately above |
| Performance / visual animations | Not measured |

The inspector tests use temporary synthetic binary headers solely to exercise rejection
of wrong architecture/platform, malformed files, unsafe paths and wrong identities.
Those fixtures are not compiled applications and are never uploaded as IPA artifacts.
Provisioning tests cover expiry, team mismatch, wildcard keychain groups, foreign groups
and unexpected capabilities. Real codesign verification still requires macOS and profiles.

First macOS run verified Xcode 27.1 (27A9275), Bazel 9.2.0, macOS 27.0.1, ARM64,
12 pinned iOS submodules, and infrastructure tests. Recorded free disk before dependencies:
37,441,654,784 bytes. These checks passed; no IPA was produced by this attempt.
Its source was `f87393a6cbc6020d4c93a2b6fc6e10c4d9e18b9e`.

After first successful compilation, record the exact commit, run URL, IPA SHA-256 and
inspection report before tagging a baseline. Physical-device claims need actual evidence.
