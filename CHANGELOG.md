# Changelog

## Unreleased — 2026-11-26

- Added explicit, source-hash-guarded unsigned device archive packaging after the first
  real macOS attempt exposed unconditional profile embedding in rules_apple.
- Normal/signed profile enforcement remains intact; two explicit unsigned features are
  required. Added regression checks and retained the failed run's complete evidence.
- Infrastructure suite passes locally (13 tests); the earlier GitHub run passed 11 tests.
- Implemented an isolated Swift/Foundation Zalgo-filter adaptation with preserved UTF-16
  positions and attributed runs. All 10 native XCTest cases passed on macOS/Swift 6.4
  in run 45711409372; integration into the iOS client remains pending the baseline gate.

## Unreleased — 2026-11-25

- Preserved Telegram-iOS history at `24638bc69bd083981b178dd1e7f921eebbf7fc46`.
- Pinned Android reference at `b4d852f48f2734a0bee1a74a0939be621612262a` (13.2.2).
- Created independent Asteri development branch and GitHub repository.
- Added manual macOS device/simulator build and release workflows, configuration
  validation, private secret setup, Mach-O/IPA inspection and regression checks.
- Corrected a relative tgcalls submodule URL so a fork checks out the official dependency.
- Preserved the obsolete upstream macOS 13 workflow as `docs/upstream-build.yml.reference`.
- Custom application features have not been ported yet.
