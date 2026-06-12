#!/usr/bin/env python3
from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLE = ROOT / "apple" / "ClawDesk"
SERVER = ROOT / "server"
DIST = ROOT / "dist"
APP_NAME = "ClawDesk"
BUNDLE_ID = "com.jannerchang.clawdesk"
VERSION = os.getenv("CLAWDESK_VERSION", "0.1.0")


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd or ROOT, check=True)


def copytree(src: Path, dst: Path, ignore: Callable[[str, list[str]], set[str]] | None = None) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=ignore)


def main() -> int:
    run(["swift", "build", "--configuration", "release", "--package-path", str(APPLE)])

    binary = APPLE / ".build" / "release" / "ClawDeskApp"
    if not binary.exists():
        raise FileNotFoundError(binary)

    DIST.mkdir(exist_ok=True)
    app = DIST / f"{APP_NAME}.app"
    if app.exists():
        shutil.rmtree(app)

    contents = app / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    shutil.copy2(binary, resources / "ClawDeskApp")
    os.chmod(resources / "ClawDeskApp", 0o755)

    copytree(
        SERVER,
        resources / "server",
        ignore=shutil.ignore_patterns(".venv", ".data", ".pytest_cache", "__pycache__", "*.pyc", "tests"),
    )

    launcher = macos / APP_NAME
    launcher.write_text(
        """#!/bin/bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RESOURCES="$APP_DIR/Resources"
APP_SUPPORT="$HOME/Library/Application Support/ClawDesk"
LOG_DIR="$HOME/Library/Logs/ClawDesk"
PORT="${CLAWDESK_PORT:-8765}"
BASE_URL="http://127.0.0.1:${PORT}"

mkdir -p "$APP_SUPPORT" "$LOG_DIR"

if ! command -v uv >/dev/null 2>&1; then
  osascript -e 'display dialog "ClawDesk requires uv to run the bundled local backend. Install uv first, then reopen ClawDesk." buttons {"OK"} default button 1 with icon caution' || true
  exit 1
fi

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

(
  cd "$RESOURCES/server"
  CLAWDESK_DB_PATH="$APP_SUPPORT/clawdesk.db" \
  CLAWDESK_HERMES_MODE="${CLAWDESK_HERMES_MODE:-auto}" \
  CLAWDESK_HERMES_TIMEOUT_SECONDS="${CLAWDESK_HERMES_TIMEOUT_SECONDS:-120}" \
  uv run uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
) >> "$LOG_DIR/server.log" 2>&1 &
SERVER_PID=$!

for _ in {1..80}; do
  if /usr/bin/curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    osascript -e 'display dialog "ClawDesk backend exited during startup. See ~/Library/Logs/ClawDesk/server.log" buttons {"OK"} default button 1 with icon caution' || true
    exit 1
  fi
  sleep 0.25
done

if ! /usr/bin/curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  osascript -e 'display dialog "ClawDesk backend did not become ready. See ~/Library/Logs/ClawDesk/server.log" buttons {"OK"} default button 1 with icon caution' || true
  exit 1
fi

CLAWDESK_BASE_URL="$BASE_URL" "$RESOURCES/ClawDeskApp"
""",
        encoding="utf-8",
    )
    os.chmod(launcher, 0o755)

    plist = {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleExecutable": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": VERSION,
        "LSMinimumSystemVersion": "14.0",
        "NSHighResolutionCapable": True,
    }
    with (contents / "Info.plist").open("wb") as f:
        plistlib.dump(plist, f)

    run(["codesign", "--force", "--deep", "--sign", "-", str(app)])
    run(["codesign", "--verify", "--deep", "--strict", str(app)])

    zip_path = DIST / f"ClawDesk-{VERSION}-macOS.zip"
    if zip_path.exists():
        zip_path.unlink()
    run(["ditto", "-c", "-k", "--keepParent", str(app), str(zip_path)])

    print(f"APP={app}")
    print(f"ZIP={zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
