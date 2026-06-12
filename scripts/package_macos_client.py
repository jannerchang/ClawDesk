#!/usr/bin/env python3
from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLE = ROOT / "apple" / "ClawDesk"
DIST = ROOT / "dist"
APP_NAME = "ClawDesk"
BUNDLE_ID = "com.jannerchang.clawdesk.client"
VERSION = os.getenv("CLAWDESK_VERSION", "0.1.0")


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd or ROOT, check=True)


def main() -> int:
    run(["swift", "build", "--configuration", "release", "--package-path", str(APPLE)])

    binary = APPLE / ".build" / "release" / "ClawDeskApp"
    if not binary.exists():
        raise FileNotFoundError(binary)

    DIST.mkdir(exist_ok=True)
    app = DIST / f"{APP_NAME}-Client.app"
    if app.exists():
        shutil.rmtree(app)

    contents = app / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    shutil.copy2(binary, resources / "ClawDeskApp")
    os.chmod(resources / "ClawDeskApp", 0o755)

    launcher = macos / APP_NAME
    launcher.write_text(
        """#!/bin/bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RESOURCES="$APP_DIR/Resources"
exec "$RESOURCES/ClawDeskApp"
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

    zip_path = DIST / f"ClawDesk-{VERSION}-macOS-client.zip"
    if zip_path.exists():
        zip_path.unlink()
    run(["ditto", "-c", "-k", "--keepParent", str(app), str(zip_path)])

    print(f"APP={app}")
    print(f"ZIP={zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
