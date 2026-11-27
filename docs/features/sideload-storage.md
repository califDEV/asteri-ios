# Explicit standalone storage variant

The owner installed the baseline with Sideloadly and observed a black screen. The
baseline requires `group.<bundle ID>` and stops initialization if its container is
unavailable. This is a source-backed hypothesis for the observed failure; the exact
on-device cause remains unconfirmed until the replacement is tested.

The standalone variant is selected by `private_container=true` in ios-build.yml.
It uses a separate `.sideload` bundle ID and `asteri-sideload` URL scheme. A compiled
Info.plist flag chooses private Application Support/Asteri storage. This is never an
automatic fallback from a missing shared account database and never migrates/deletes
the full variant's data. The build omits extensions, App Groups and APNs entitlements;
runtime initialization also rejects an unexpectedly embedded app extension.

PasscodeConfiguration explicitly chooses privateApplication credential storage. The
existing validated per-application keychain group is used for credentials and biometric
items. Shared-group requests fail in that mode, missing own-keychain access still fails,
extensions cannot select it, and the configuration cannot change after initialization.
The default shared mode and its keychain/group checks retain their original behavior.
Encryption, biometric access-control policy, account authorization, transport and logout
gates are not changed. Background URL sessions use the private application's container.

Storage setup errors now install an actionable native screen on the UIWindow, before
the custom window has its main controller, rather than relying on an alert presented
through an incomplete controller hierarchy. This error UI is also pending visual checks.

Five native scope scenarios exercise the production passcode sources in a host target;
the account-manager adapter is checked by full application builds. The standalone IPA
must contain no extensions and must carry the correct mode flag. Simulator checks
require a real process, initialized private directory, screenshots and launch video.
These checks do not replace signing and launch tests on the owner's physical iPhone.

Current state: implementation prepared; native scope, full build and simulator results
must be recorded before describing the device problem as fixed.

Expected recorded frames before the startup replay: normal standalone launch reaches
the real unauthenticated application UI, with no storage warning or blank settled page.
The injected missing-group case shows the native Asteri heading and actionable Sideload
instruction centered inside the content band. Both scenarios use the same compiled app;
only a staging copy is changed for the failure case, with no delivery-IPA modification.
Labels must remain readable against the system background and not overlap or clip.
