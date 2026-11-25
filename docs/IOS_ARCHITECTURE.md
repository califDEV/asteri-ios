# Native iOS architecture

Status: baseline preparation. No custom application module has been integrated yet.
Retain Telegram-iOS's launch/extension targets in `Telegram/BUILD`, native libraries in
`submodules/`, third-party dependencies in `third-party/`, and official Bazel/Make.py entry.
The current upstream includes Swift, Objective-C, C/C++, Rust, and native widget runtimes;
its existing boundaries and security invariants remain authoritative.

Proposed custom module boundaries after a verified baseline:

| Module | Responsibility | Integration |
|---|---|---|
| AsteriPreferences | Typed/versioned settings and migrations | AccountManager shared preferences or account-scoped engine data; no unrelated session access |
| AsteriSettingsUI | General/Appearance/Chats/Plugins settings and About attribution | SettingsUI entry; ItemListUI, PresentationData, native navigation/theme updates |
| AsteriFeatures | Pure formatting/action policy utilities plus thin adapters | Existing chat/list/profile/media components; no duplicated MTProto client |
| AsteriPluginAPI | Versioned value-based event/menu/settings APIs | Explicit TelegramEngine operations on a host-owned queue; gate account access |
| AsteriPluginRuntime | Reviewed runtime, lifecycle, import validation and logging | Off main thread; no raw Java objects, Android reflection, or app-session objects |

These names are design boundaries, not claimed implemented modules. Read the relevant
upstream CLAUDE.md before editing a subsystem. TelegramCore must remain independent of
UIKit; UI consumers use existing TelegramEngine facade types. Do not add raw Postbox imports
or widen allowlists without an actual architectural need and review.

UI settings must immediately control real behavior, persist across restart, and react to
presentation/theme changes. Message edits, sends, deletes, peer permissions, secret-chat
handling, authentication, transport security and authorization stay on upstream paths.
Safe area/reserved corners and keyboard behavior use existing layout APIs.

Keep custom integration seams small and sync upstream into a feature branch before
merging. `upstream` retains the official URL. The sole baseline source change outside
documentation/CI is an optional `.bazelrc` import and the absolute official tgcalls URL;
they do not alter the application's messaging behavior.

Performance gates are baseline-relative measurements, currently unmeasured: cold/warm
launch, resident memory, scrolling frame time, energy, player behavior, background work,
IPA size, plugin event latency and queue saturation. No guarantee about preserving upstream
performance can be made before these measurements exist.
