# Native iOS architecture

Status: first app integration after the verified ARM64 baseline (2026-11-28).
`submodules/AsteriFeatures` owns Foundation-only text utilities and typed settings.
`TelegramUIPreferences/AsteriSettings.swift` persists them through AccountManager shared
data under key 100000. Initial/live presentation data carry the value into text-bubble
layout, including theme and bubble-free copies. Selection retains the unfiltered source
and protected-content eligibility gates. `submodules/AsteriSettingsUI` owns the native
Appearance → Asteri screen. Tests/AsteriHarness exercises the production screen and
preference writer with an empty database. Full app and visual validation are in progress;
account and physical-device behavior remain unverified.
Retain Telegram-iOS's launch/extension targets in `Telegram/BUILD`, native libraries in
`submodules/`, third-party dependencies in `third-party/`, and official Bazel/Make.py entry.
The current upstream includes Swift, Objective-C, C/C++, Rust, and native widget runtimes;
its existing boundaries and security invariants remain authoritative.

Remaining proposed custom module boundaries:

| Module | Responsibility | Integration |
|---|---|---|
| AsteriPreferences | Typed/versioned settings and migrations | AccountManager shared preferences or account-scoped engine data; no unrelated session access |
| AsteriSettingsUI | General/Appearance/Chats/Plugins settings and About attribution | SettingsUI entry; ItemListUI, PresentationData, native navigation/theme updates |
| AsteriFeatures | Pure formatting/action policy utilities plus thin adapters | Existing chat/list/profile/media components; no duplicated MTProto client |
| AsteriPluginAPI | Versioned value-based event/menu/settings APIs | Explicit TelegramEngine operations on a host-owned queue; gate account access |
| AsteriPluginRuntime | Reviewed runtime, lifecycle, import validation and logging | Off main thread; no raw Java objects, Android reflection, or app-session objects |

These table rows are design boundaries, not completed modules. Read the relevant
upstream CLAUDE.md before editing a subsystem. TelegramCore must remain independent of
UIKit; UI consumers use existing TelegramEngine facade types. Do not add raw Postbox imports
or widen allowlists without an actual architectural need and review.

UI settings must immediately control real behavior, persist across restart, and react to
presentation/theme changes. Message edits, sends, deletes, peer permissions, secret-chat
handling, authentication, transport security and authorization stay on upstream paths.
Safe area/reserved corners and keyboard behavior use existing layout APIs.

Keep custom integration seams small and sync upstream into a feature branch before
merging. `upstream` retains the official URL. The baseline and feature revisions retain
the pinned submodules. Display filtering, the preference pipeline, native settings and
independent identity are explicit source changes; transport and message storage stay
on the upstream paths.

Performance gates are baseline-relative measurements, currently unmeasured: cold/warm
launch, resident memory, scrolling frame time, energy, player behavior, background work,
IPA size, plugin event latency and queue saturation. No guarantee about preserving upstream
performance can be made before these measurements exist.
