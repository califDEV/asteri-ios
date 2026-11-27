# Asteri native feature utilities

Native Swift/Foundation adaptation of exteraGram's ZalgoFilter. Based on exteraGram
([source and attribution](https://github.com/exteraSquad/exteraGram)), without endorsement.
Original copyright and GPL/additional terms are retained in this directory.

The production sources are integrated into message text/caption layout, with an immutable
settings snapshot persisted through AccountManager and a native Appearance → Asteri screen.
`AsteriDisplayText` keeps the unmodified source for selection/copy/quote/share operations.
Full app compilation, recorded-frame inspection and physical-device behavior are separate
verification gates. Android's broader emoji-rendered surfaces are not all covered yet.

The implementation uses the original thresholds/ranges/control policy, replaces entire
offending combining-mark sequences, and preserves UTF-16 offsets and attributed runs.
Use it only for display text; never change persisted or outgoing messages. Unicode
category tables can differ between Android and iOS versions and need device coverage.

Run `swift test --package-path submodules/AsteriFeatures`. Tests cover Latin/Arabic marks,
mixed limits, bidi controls, emoji, supplementary scalars, disabled mode, attributes,
unchanged input and long input. Results from the dedicated macOS native-text CI job
must be recorded separately from Python infrastructure checks.

Verified in [run 45712163625](https://github.com/califDEV/asteri-ios/actions/runs/45712163625):
10 scenarios passed in both debug and release on macOS/Swift 6.4, and the source compiled
as a module for `arm64-apple-ios15.0` with the iPhoneOS SDK. App integration, simulator
rendering and physical-device behavior were not established by that earlier prototype run.
