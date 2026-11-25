# Android implementation audit

Snapshot: 2026-11-25. **In progress**, not a completed audit of every behavior.

exteraGram pin: `b4d852f48f2734a0bee1a74a0939be621612262a` (13.2.2 / 7303).
Official Android comparison: `21f7d109da6ab3506c9e9577f98c6a38771ab335`, also 13.2.2 / 7303.
iOS base: `24638bc69bd083981b178dd1e7f921eebbf7fc46` (app 13.2).
The references are separate checkouts and are not linked into the iOS build.

`scripts/asteri/audit_android.py` compares complete Git trees by blob/mode and scans
the checked-out source for preference consumers and SDK APIs. Its machine-readable
evidence is [audit/android-inventory.json](audit/android-inventory.json). It found:

- 585 Java/Kotlin files under the custom `com.exteragram.messenger` package across flavors.
- 175 delegated ExteraConfig preferences; 32 Python source modules in `plugins-pysdk/src`.
- Against the matching official release: 2,804 paths added, 846 modified, 1,243 deleted.
  These are file deltas, including resources/build metadata, not counts of features.
  An unmodified blob is strong equality evidence; changed blobs still require semantic review.

To reproduce from the iOS root:

```text
python scripts/asteri/audit_android.py --android ../references/exteraGram-Android --official ../references/Telegram-Android --docs docs
```

The source remains Telegram Android with invasive call sites in `org.telegram.*`,
custom controllers/UI under `com.exteragram.messenger`, and native JNI dependencies.
`full` and `lite` are separate source flavors: the full flavor embeds Chaquopy and
hooking; the lite flavor has alternate plugin classes and no full runtime.
This difference must not be mistaken for a single universal plugin implementation.

Implementation findings already read directly:

| Area | Actual source / behavior | Port implication |
|---|---|---|
| Preferences | `ExteraConfig.kt`, `config/PrefClasses.kt`: delegated typed values, lazy in-memory cache, SharedPreferences storage via apply, backup-key registration; sanitized integer delegates | Native typed persistent settings; keep stable encoded keys; migrate values deliberately |
| Settings entry | `preferences/MainPreferencesActivity.kt`: General, Appearance, Chats, Plugins (conditional engine availability), Other, community/source links | Native settings entry needs real controller wiring; preserve required attribution |
| General/profile | `preferences/GeneralPreferencesActivity.kt`: number precision, seconds, haptics, Zalgo, transfer boost, hide local phone, peer ID/DC, profile tab, archive behavior | Hiding the phone is local presentation, not a server privacy guarantee; profile/DC requires iOS engine mapping |
| Gestures | `utils/chats/DoubleTapUtils.java`: incoming/outgoing action indexing differs; outgoing includes edit. `SwipeAction.java`: ordered, de-duplicated actions persisted as IDs | Preserve semantics with native gesture callbacks and existing send/edit/delete eligibility gates |
| Text safety | `utils/text/ZalgoFilter.java`: detects excess nonspacing/enclosing marks (2 in listed Zalgo ranges, 4 in other scripts), replaces entire offending sequence and bidi controls with U+2060 while preserving UTF-16 length/spans | Do not simply strip all accents or normalize sent messages; port display sanitation and test multilingual/entity offsets |
| Translation | `translator/TranslationProviders.kt`: Telegram, Google, Yandex, Microsoft; provider selects chat translation availability | External providers disclose text to their endpoints; need explicit choice and native request layer; retain Telegram rules |
| Chat/menu customization | `ExteraConfig.kt`, `preferences/chats/ChatsPreferencesActivity.kt`, `utils/chats/*`: double tap, swipe actions, reaction visibility, stickers, keyboard behavior, repeat/save/details/context-menu options | Consumer paths are indexed in the matrix; permission/destructive action behavior still needs end-to-end audit |
| Appearance | `ExteraConfig.kt`, `preferences/appearance/*`, `utils/ui/*`: corners, icon packs, separators, tab counters, header blur/glass, spring/back transitions, drawer/tablet behavior | Android drawables and predictive back do not port directly to UIKit; adapt interaction and assets |
| Media | Preferences expose HD/original quality, camera choice/stabilization/mirroring/zoom, seek duration, minimization pause; `utils/media/*` contains subtitle and media fingerprint helpers | AVFoundation/PhotoKit/AVAudioSession integration and hardware checks are required; preference discovery is not media testing |
| Export | `export/*` plus format/media/size/full-chat configuration in ExteraConfig | Map queries and media reads to TelegramCore; export via an explicitly chosen app/document location |
| Plugins | `src/full/.../plugins/PythonPluginsEngine.kt`, `PluginsController.kt`, hooks/xposed/pip/catalog classes; `plugins-pysdk/src/base_plugin.py` | See PLUGIN_COMPATIBILITY; loading Python alone cannot satisfy the SDK |
| Elyx packages | `plugins-pysdk/src/elyxcore/_plugin.py`, `_plugin_engine.py`: elyx/eaf packages or directories; metadata/refmap/assets/strings/wheels and lifecycle | Distinct package format needs its own importer and archive validation |
| External services | `api/network/ApiClient.kt` targets `https://api.exteragram.app/api/v1/`; other modules include AI, exchange rates, remote config, lyrics and updates | Endpoint inventory/consent review remains open. No extera network request has been added to the iOS app |
| Analytics | `useGoogleAnalytics` defaults false; `useGoogleCrashlytics` follows beta status in ExteraConfig | Do not transfer analytics into the fork silently |
| Languages/assets | `crowdin.yml`, `res/values*`, `res-solar`, `res-remix`, app icon directories | String/asset license and attribution audit required before resource reuse; original icons cannot be modified-app identity |

Paths above are relative to Android's `TMessagesProj/src/main/java/com/exteragram/messenger/`
unless explicitly prefixed. Exact preference declaration/consumer links at the source pin
are in [FEATURE_MATRIX.md](FEATURE_MATRIX.md).

Remaining audit work: all changed `org.telegram.*` call sites, exhaustive network endpoints,
AI/on-device runtime and ad-block implementations, animation measurements, localization
coverage, resource licenses, every experimental tool, plugin catalogs/update trust paths,
and behavior tests. Source paths in the inventory are leads, not audited functional parity.
