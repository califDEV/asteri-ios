# Known limitations and current evidence

Updated 2026-11-28. This is an incomplete port, not a release-ready client.

A real unsigned ARM64 baseline IPA was compiled and inspected in successful
[run 45715952913](https://github.com/califDEV/asteri-ios/actions/runs/45715952913).
It requires iOS 15.0+ and signing before installation. See TEST_REPORT for exact evidence.

- Zalgo protection is integrated in the application source, with a shared persistent
  setting and native screen. Fourteen native scenarios passed; new full-app and recorded
  visual checks are running. This does not establish feature parity or device behavior.
- Android audit includes matching-release file comparison and a 206-preference source
  inventory; exhaustive semantic/behavioral/resource/network audit remains open.
- Device-targeted compilation passed. Simulator launch, login, chats, sending/receiving, voice/media, themes,
  restart, accessibility, animations and performance require their actual test records.
  Infrastructure unit tests establish none of these app behaviors.
- No iOS Plugin Engine, Python runtime or existing-plugin execution is implemented.
  Java/Xposed/ART hooks are unsupported as written; full compatibility is not claimed.
- The published baseline retains upstream identity. The new source uses Asteri's own
  name and vector icon, omits upstream alternate app icons, and includes attribution.
- The owner reports a black screen after installing the baseline with Sideloadly on
  iOS 27. An explicit standalone variant is implemented and its builds/launch checks
  are running. No successful physical-device startup is claimed yet.
- Unsigned IPA installation is not automatic. Full Telegram App Groups/extensions/push
  capabilities may not be available under a free Apple account; paid signing material
  has not been supplied. No certificate or Apple service has been purchased.
- Push delivery also needs server-side APNs integration for the client's bundle/team;
  merely signing an app is not evidence that Telegram notifications will work.
- The published full baseline requires `group.<bundle ID>` and stops initialization
  when its container is unavailable. The new explicit standalone variant uses private
  storage and its own keychain group, without extensions; normal shared-mode behavior
  is retained. Builds and scope/launch tests are pending. Unavailable storage now has an
  actionable error page in source; its recorded-frame verification is still pending.
- Standard hosted runner memory/disk/time may constrain a cold build; actual logs decide
  feasibility. No paid runner or macOS VM is configured.
- Source history is retained; the current partial local clone fetches historical blobs
  on demand. Required iOS submodules are pinned and initialized. Android's optional
  QuickJS `test262` suite is intentionally disabled by its upstream submodule config
  and is not an app build dependency.

See PLUGIN_COMPATIBILITY for concrete platform gaps and BUILD_GUIDE for signing modes.
The baseline compile and IPA inspection are established; physical-device behavior,
feature parity and a final client release remain unverified.
