# Zalgo protection: first app integration

Android reference: pinned exteraGram `b4d852f48f2734a0bee1a74a0939be621612262a`.
`ExteraConfig.kt:216` defaults to enabled. `utils/text/ZalgoFilter.java` replaces entire
runs above two marks in Zalgo ranges / four elsewhere, and bidi controls, with U+2060.
`org/telegram/messenger/Emoji.java:617,667` applies it after emoji processing.

The production Swift module now lives in `submodules/AsteriFeatures`. A fork-owned
AccountManager shared-data key stores the setting. Initial and live presentation data,
including bubble-free mode and presentation copies, carry its value into text bubbles.
The original attributed source remains available to copy/share/lookup and quote paths;
the existing protected-content and secret-chat checks remain on their upstream paths.

Scope: message text/captions rendered by ChatMessageTextBubbleContentNode. Other Android
surfaces, InstantPage rich messages, chat-list snippets, names and notification text are
not covered by this first integration. Category-table parity across OS versions remains
unverified. No server, transport, account, persisted-message or sending behavior changes.

The native screen is Appearance → Asteri, with English, Russian and Ukrainian strings,
an immediate preview and source attribution. Its context-free factory is the same one
used by the separate loginless visual harness; the harness uses the production preference
writer with a real empty AccountManager database. It never opens a Telegram account.

## Expected recorded frames, before verification

- Initial switch is on and preview reads cleanly; ordinary Cyrillic, accents and emoji
  remain visible. Labels and switch fit within the content band, with no clipped rows.
- Toggling off moves the native thumb to the leading side and restores the sample's
  combining marks. Toggling on restores the clean preview. Row changes must not overlap.
- After termination/relaunch the last disabled value and preview remain disabled.
- Dark/light changes recolor the entire list and navigation while retaining the value.
- Home-screen icon is Asteri's independent white star on a violet orbit, not a paper plane.

Record `simctl io recordVideo` without frame-rate conversion. Export frames in original
order and label them with `ffprobe` presentation timestamps. Inspect the transition and
settled frames before marking visual verification complete. This harness does not prove
real-chat rendering, login, physical-device installation or account behavior.

Verification results: pending the new CI runs. Source integration alone is not a pass.
