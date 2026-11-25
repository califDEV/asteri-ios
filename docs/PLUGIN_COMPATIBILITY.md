# Plugin engine and Python SDK audit

Status: **research; no iOS Plugin Engine or Python runtime implemented, zero existing
plugins verified on iOS**. Main source pin and AST-discovered BasePlugin method list are
in `audit/android-inventory.json`.

Android implementation:

- `PythonPluginsEngine.kt` starts Chaquopy with `AndroidPlatform(ApplicationLoader...)`,
  bootstraps a packaged SDK and handles signed SDK updates/restoration. These are Android
  runtime integrations, not portable CPython calls.
- `.plugin` files provide `__id__`, `__name__`, description/author/version/icon,
  requirements and version metadata. The source metadata parser uses tokenization/AST
  rather than importing a plugin simply to read metadata. IDs must match
  `^[a-zA-Z][a-zA-Z0-9_-]{1,31}$`; app/SDK requirements are checked.
- BasePlugin lifecycle includes load/unload, cleanup registration, stop events and app
  lifecycle notifications. Event contracts cover pre/post requests, individual/batched
  updates and message sending. Hook strategies include DEFAULT, CANCEL, MODIFY,
  MODIFY_FINAL, and results carry actual Android/Telegram objects.
- UI API includes settings (switch/input/selector/header/divider/text/custom), menu items
  in message/drawer/main/chat/profile contexts, callbacks/conditions/priorities, logging,
  account client helpers and persistence.
- Hooking includes Xposed method/construction replacement and instruction-level partial
  call-site, field-read/write, string-constant and return-value hooks. The bundled
  `examples/partial_hooks_demo.plugin` addresses Java members such as DialogCell and
  ChatMessageCell; it cannot target Swift functions as written.
- Dependencies use Android pip controller/wheels and Java interop. Elyx (`.elyx`/`.eaf`)
  additionally supports package structures, metadata, refmaps, assets, localization,
  wheels and a separate loader. Import/archive checks must cover both formats.

| Contract | iOS assessment | Required native alternative | Verified compatibility |
|---|---|---|---|
| Metadata and pure Python algorithms | Potentially portable | Nonexecuting importer and embedded runtime with fixtures | None |
| BasePlugin import | Not currently portable: imports Java, Xposed and Android host classes at module load | New compatibility module with explicit supported API | None |
| Load/unload/settings/logging | Reimplementable | Versioned lifecycle, persistent settings, error reporting, deterministic cleanup | None |
| MTProto request/update/send hooks | Android object models cannot pass through unchanged | Typed DTOs and explicit TelegramEngine events; preserve security checks | None |
| Menu/settings widgets | Android Views/Fragments/custom factories unavailable | Native ItemListUI/menu adapters; reject unsupported custom views | None |
| Java/Xposed/ART/partial hooks | No corresponding Android runtime or target classes on iOS | Explicit extension points for specific behaviors, plugin source changes | Unsupported as written |
| Native pip wheels | Android ABI incompatible; new unsigned executable libraries cannot be loaded like desktop wheels | Reviewed iOS libraries compiled, packaged and signed with the app | None |
| Permission/data isolation | App sandbox isolates applications, not Python modules in one interpreter | Capability-based host API and separate per-plugin storage; security design still open | None |

[CPython officially supports embedded Python on iOS](https://docs.python.org/3/using/ios.html),
including special packaging for native extension modules. This makes interpreter embedding
plausible; it does not supply Chaquopy, a JVM, Android SDK or Xposed. No runtime dependency
has been vendored before a baseline exists. Any vendored runtime needs a source pin,
checksums, licenses, a Bazel target and device/simulator builds without JIT assumptions.

A proposed compatibility layer can preserve metadata and selected high-level events,
settings and menu declarations. It cannot emulate arbitrary Java/Android class semantics.
Stub Java modules which silently return values would misrepresent compatibility and are
excluded. Missing APIs must fail clearly before enabling a plugin.

Security is unresolved for arbitrary untrusted Python: separate module globals, filtered
imports and capability checks alone do not form an OS security boundary within CPython.
Separate data directories are organizational separation, not protection from a malicious
plugin that can call unrestricted file APIs. Do not advertise full isolation until a
defensible restricted execution boundary is implemented and tested. Never expose Telegram
session paths, keys, account objects or unrestricted network/filesystem capability by default.

For App Store distribution, [Apple guideline 2.5.2](https://developer.apple.com/app-store/review/guidelines/#software-requirements)
restricts code downloaded to change application functionality. Sideloading and App Store
distribution need separate policy assessments; signing/sandbox constraints still apply.
Bundling an interpreter is not automatic permission for a general downloadable plugin system.
The main client must work without jailbreak. Pure/native fixture success, existing plugin
success and physical-device success must be recorded separately.

## Candidate for stronger Python isolation (research, not implemented)

The pinned iOS base already vendors **WAMR 2.4.5** in `third-party/wamr/BUILD`, configured
for an interpreter, with JIT/AOT, shared memory and thread manager disabled. WASI is
enabled. Its exported API includes directory mappings, network/address lookup pools,
instance memory limits and termination; their behavior with Python remains untested.
The existing call engine's trusted-WASM loader and its security restrictions must remain
unchanged. Message widgets use a separate native QuickJS runtime, not a Python engine.

[CPython's official WASI build instructions](https://github.com/python/cpython/blob/main/Platforms/WASI/README.md)
document cross-compiling the interpreter to WebAssembly. **Inference to investigate**:
a separately instantiated Python/WASI interpreter could offer a more defensible memory
and host-resource boundary than unrestricted native CPython subinterpreters, while
reusing the already-vendored native interpreter. This would execute plugin logic inside
the native iOS app and would not provide an Android runtime or Android hook compatibility.

Before adopting this approach, prove all of the following with actual builds/tests:

- A pinned/checksummed Python/WASI build and standard library run on this exact WAMR
  version and feature configuration on macOS, iOS simulator and physical ARM64 iPhone.
- Per-plugin instances expose only their own data directory and read-only runtime data;
  attempted traversal/symlink escapes, cross-plugin reads and session-file access fail.
- Network and native imports are denied by default; opt-in requests go through a bounded
  host capability API. A module import must not grant arbitrary file/socket access.
- Infinite loops, allocator pressure, exceptions and unload can be terminated without
  touching the UI thread or changing the existing call engine's performance/security flags.
- Memory/startup/event overhead and unsupported standard-library/native-wheel behavior
  are measured. Neither WAMR availability nor Python's WASI support proves these properties.

Java/Xposed/ART-dependent plugins would still need source changes or explicit supported
DTO/event adapters. No existing plugin execution, runtime isolation or compatibility is
claimed by this research. App Store policy assessment remains separate from IPA sideloading.
