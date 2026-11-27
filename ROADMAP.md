# Asteri port roadmap

Updated 2026-11-26. Completion requires actual app and device evidence.

| Phase | State | Exit criterion |
|---|---|---|
| 0 Environment | Complete | Git, portable gh, Python and GitHub authentication checked |
| 1 Sources | Complete for required sources | Both repositories and build submodules checked out at pinned commits |
| 2 Android audit | In progress | Implementation-based matrix, plugin/API audit, Android upstream comparison |
| 3 Baseline iOS build | Complete | Run 45715952913 succeeded; ARM64 device IPA inspected; source c282490f0dd2e804f9fe91e8aed9669a3d46e07c, tag baseline-ios-13.2-20261126 |
| 4 Custom architecture | In progress | AsteriFeatures, AsteriSettingsUI and AccountManager preference adapter integrated; full build/visual checks pending |
| 5 Feature ports | In progress | Zalgo message-display integration; 14 native scenarios passed; broader surfaces and app/device checks pending |
| 6 Native interface | In progress | Independent identity and native settings source added; recorded-frame verification pending |
| 7 Plugins | Research | Tested supported subset; Android-specific hooks explicitly unsupported |
| 8 QA/performance | Pending | Simulator/device scenarios, crashes and measurements |
| 9 Final IPA | Pending | Final ARM64 artifact, entitlements and installation validation |
| 10 Release | Pending | Source, verified artifact, checksum, limits and test report published |

Build infrastructure checks do not satisfy Phase 3. Successful compilation does not
satisfy login, messaging, media, plugin, performance or physical-device testing.

First real macOS baseline attempt: [45708379459](https://github.com/califDEV/asteri-ios/actions/runs/45708379459).
Infrastructure suite: [45708384597](https://github.com/califDEV/asteri-ios/actions/runs/45708384597) passed.

Verified baseline: [45715952913](https://github.com/califDEV/asteri-ios/actions/runs/45715952913),
80,671,077-byte unsigned IPA, iOS 15.0+, SHA-256
`1b3e71d88ca81dc9e420672223f24b7a2c13263e50c6aeb3136aec8dba3f1700`.
This is the Telegram-based compilation baseline; no app-integrated extera features or
physical-device installation are established by this milestone.
