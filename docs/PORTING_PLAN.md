# Porting sequence

The roadmap tracks phase completion. The baseline commit adds runnable infrastructure;
it does not count as a successful iOS build or a feature port.

1. Complete source/provenance inventory and obtain a verified official ARM64 baseline on
   the standard GitHub macOS runner. Diagnose full logs for each failure. Do not override
   Xcode/Bazel pins or fabricate provisioning to make checks green.
2. Commit/tag the successful source revision as `baseline-ios-<date>-<run>`, link its run
   and inspection report, then preserve a reference for size/performance comparisons.
3. Introduce typed persistent preferences and a native settings entry with About attribution.
   Start with audited local formatting/display features; test the actual consumer behavior.
4. Port chat actions and profile/menu presentation using existing eligibility and engine APIs.
   Test incoming/outgoing differences, protected content, secret chats, and entity offsets.
5. Port appearance in native components, including light/dark/system themes and motion.
   For every visual change follow AGENTS.md's recorded-frame verification requirement.
6. Port media, translation, export and optional external services after endpoint/privacy review.
   Hardware capabilities and background execution need actual-device evidence.
7. Prototype embedded Python separately, establish an honest compatibility/permission
   boundary, then implement lifecycle, manager UI, event adapters and supported fixtures.
   Do not offer installs of packages the engine cannot execute correctly.
8. Run simulator scenarios and a physical iPhone installation/auth/message/media/restart
   checklist. Keep crash logs and measured results, then build/release the final source.

Each feature record must include Android behavior evidence, dependency mapping, native
implementation, meaningful tests, build run, source commit, limitations and physical-device
status. Unsupported platform behavior needs a researched alternative and a concrete reason.
The lexical preference inventory is the initial queue, not an assertion that all features
are known or that Phase 2 is complete.
