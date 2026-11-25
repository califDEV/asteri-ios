# Asteri port roadmap

Updated 2026-11-25. Completion requires actual app and device evidence.

| Phase | State | Exit criterion |
|---|---|---|
| 0 Environment | Complete | Git, portable gh, Python and GitHub authentication checked |
| 1 Sources | Complete for required sources | Both repositories and build submodules checked out at pinned commits |
| 2 Android audit | In progress | Implementation-based matrix, plugin/API audit, Android upstream comparison |
| 3 Baseline iOS build | In progress | Official Make.py succeeds; real device ARM64 IPA inspected; commit/tag and run URL recorded |
| 4 Custom architecture | Pending Phase 3 | Isolated native modules and persistent preferences design |
| 5 Feature ports | Pending | Each behavior implemented, tested, built, documented, committed |
| 6 Native interface | Pending | Independent branding, settings, themes, visual simulator evidence |
| 7 Plugins | Research | Tested supported subset; Android-specific hooks explicitly unsupported |
| 8 QA/performance | Pending | Simulator/device scenarios, crashes and measurements |
| 9 Final IPA | Pending | Final ARM64 artifact, entitlements and installation validation |
| 10 Release | Pending | Source, verified artifact, checksum, limits and test report published |

Build infrastructure checks do not satisfy Phase 3. Successful compilation does not
satisfy login, messaging, media, plugin, performance or physical-device testing.

First real macOS baseline attempt: [45708379459](https://github.com/califDEV/asteri-ios/actions/runs/45708379459).
Infrastructure suite: [45708384597](https://github.com/califDEV/asteri-ios/actions/runs/45708384597) passed.
