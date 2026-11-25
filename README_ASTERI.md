# Asteri iOS port (work in progress)

Independent native iOS port research based on [exteraGram](https://github.com/exteraSquad/exteraGram)
and [Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS).
This project is not endorsed by either upstream project.

The application working name is **Asteri**. The directory name `exteraGram-iOS`
identifies the porting workspace, not permission to use exteraGram's trademark.
Upstream source, history, notices, and compilation README are retained.

Current stage: establishing a reproducible baseline build, before custom feature ports.
No iPhone validation, feature parity, or Python plugin compatibility is claimed.
Baseline artifacts retain upstream app identity until Phase 6 and are development evidence.

See [ROADMAP](ROADMAP.md), [build guide](docs/BUILD_GUIDE.md), and the source audit
documents under `docs/`. Builds run only when manually dispatched; macOS builds
use the standard `xcode-27` runner. No paid runner is configured.
