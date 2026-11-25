# AsteriText native prototype

Native Swift/Foundation adaptation of exteraGram's ZalgoFilter. Based on exteraGram
([source and attribution](https://github.com/exteraSquad/exteraGram)), without endorsement.
Original copyright and GPL/additional terms are retained in this directory.

This package is an isolated prototype, **not integrated into Telegram-iOS yet**.
It does not establish that the app's Zalgo option has been ported end to end.
The baseline app build must succeed before large feature integration.

The implementation uses the original thresholds/ranges/control policy, replaces entire
offending combining-mark sequences, and preserves UTF-16 offsets and attributed runs.
Use it only for display text; never change persisted or outgoing messages. Unicode
category tables can differ between Android and iOS versions and need device coverage.

Run `swift test --package-path prototypes/AsteriText`. Tests cover Latin/Arabic marks,
mixed limits, bidi controls, emoji, supplementary scalars, disabled mode, attributes,
unchanged input and long input. Results from the dedicated macOS native-text CI job
must be recorded separately from Python infrastructure checks.

Verified in [run 45712163625](https://github.com/califDEV/asteri-ios/actions/runs/45712163625):
10 scenarios passed in both debug and release on macOS/Swift 6.4, and the source compiled
as a module for `arm64-apple-ios15.0` with the iPhoneOS SDK. App integration, simulator
rendering and physical-device behavior remain unverified.
