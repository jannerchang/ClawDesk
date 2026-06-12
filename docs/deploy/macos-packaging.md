# ClawDesk macOS packaging

This is the local distributable packaging path for the current ClawDesk prototype.

## Build a package

From the repo root:

```bash
./scripts/package_macos.py
```

Outputs:

```text
dist/ClawDesk.app
dist/ClawDesk-0.1.0-macOS.zip
```

The `.app` is ad-hoc signed with `codesign --sign -`, then zipped with `ditto --keepParent`.

## What the app bundle contains

```text
ClawDesk.app/
  Contents/
    MacOS/ClawDesk              launcher script
    Resources/ClawDeskApp       SwiftUI release executable
    Resources/server/           bundled FastAPI backend source + uv.lock
```

On launch, the wrapper:

1. starts the bundled FastAPI backend on `127.0.0.1:${CLAWDESK_PORT:-8765}`;
2. stores the app database at `~/Library/Application Support/ClawDesk/clawdesk.db`;
3. writes backend logs to `~/Library/Logs/ClawDesk/server.log`;
4. waits for `/health`;
5. starts the SwiftUI client with `CLAWDESK_BASE_URL` pointed at the local backend;
6. stops the backend when the client exits.

## Runtime requirements

Current local package still requires these to be installed on the target Mac:

- macOS 14+
- `uv`
- network access or cached uv environment for first backend start
- local `hermes` CLI if real Hermes replies are desired

If `hermes` is not available, backend `auto` mode falls back to stub output. For strict real Hermes mode:

```bash
CLAWDESK_HERMES_MODE=cli CLAWDESK_HERMES_FALLBACK_TO_STUB=0 open dist/ClawDesk.app
```

For a different backend port:

```bash
CLAWDESK_PORT=8877 open dist/ClawDesk.app
```

## Release verification

Before calling a build publishable, run:

```bash
swift build --package-path apple/ClawDesk
cd server && uv run pytest
cd ..
./scripts/smoke.py
./scripts/smoke_real_hermes.py
./scripts/package_macos.py
codesign --verify --deep --strict dist/ClawDesk.app
unzip -l dist/ClawDesk-0.1.0-macOS.zip | head
```

## Current packaging boundary

This is a usable local macOS software package, not a notarized public release:

- no Apple Developer ID signing yet;
- no notarization yet;
- no DMG installer yet;
- backend is bundled as source and launched via `uv`, not frozen into a standalone binary;
- no auto-update channel yet.

Those are next release-hardening steps.
