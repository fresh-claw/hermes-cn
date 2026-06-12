#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-2026.06.12.1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_WEB_DIR="${SITE_WEB_DIR:-$ROOT/../../promo_work/hermes-zh-cn/web}"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'missing command: %s\n' "$1" >&2
    exit 1
  }
}

need bash
need python3
need shasum
need unzip

cd "$ROOT"

bash -n install.sh
bash -n install.command
python3 -m json.tool platforms.json >/dev/null

python3 - "$VERSION" <<'PY'
import base64
import hashlib
import json
import re
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

version = sys.argv[1]
root = Path.cwd()

install_sh = (root / "install.sh").read_text(encoding="utf-8")
if f'PACKAGE_VERSION="{version}"' not in install_sh:
    raise SystemExit("install.sh version mismatch")

match = re.search(r'DATA = """\n(.*?)\n"""', install_sh, re.S)
if not match:
    raise SystemExit("embedded payload not found")
payload = base64.b64decode("".join(line.strip() for line in match.group(1).splitlines()))

with tempfile.NamedTemporaryFile(suffix=".tar.gz") as handle:
    handle.write(payload)
    handle.flush()
    with tarfile.open(handle.name, "r:gz") as tar:
        manifest = json.load(tar.extractfile("packages/0.16.x/zh-CN/manifest.json"))
        package = tar.extractfile("packages/0.16.x/zh-CN/zh-cn.min.json").read()
if manifest["version"] != version:
    raise SystemExit("embedded manifest version mismatch")
if hashlib.sha256(package).hexdigest() != manifest["files"][0]["sha256"]:
    raise SystemExit("embedded package sha mismatch")

with zipfile.ZipFile(root / "hermes-macos-installer.zip") as archive:
    zipped_install = archive.read("install.sh").decode("utf-8")
    zipped_command = archive.read("install.command").decode("utf-8")
if f'PACKAGE_VERSION="{version}"' not in zipped_install:
    raise SystemExit("mac zip install.sh version mismatch")
if f"v{version}" not in zipped_command:
    raise SystemExit("mac zip install.command version mismatch")

exe_bytes = (root / "Hermes-zh-CN-Setup.exe").read_bytes()
if f"v{version}".encode() not in exe_bytes:
    raise SystemExit("windows exe embedded version mismatch")

print("embedded payload ok")
print("mac zip ok")
print("windows exe marker ok")
PY

if [ -d "$SITE_WEB_DIR" ]; then
  for file in \
    "$SITE_WEB_DIR/latest.json" \
    "$SITE_WEB_DIR/agent.json" \
    "$SITE_WEB_DIR/platforms.json" \
    "$SITE_WEB_DIR/api/resolve" \
    "$SITE_WEB_DIR/api/resolve.sample.json" \
    "$SITE_WEB_DIR/packages/0.16.x/zh-CN/manifest.json"; do
    python3 -m json.tool "$file" >/dev/null
  done
  bash -n "$SITE_WEB_DIR/install.sh"
  bash -n "$SITE_WEB_DIR/install.command"
  cmp -s Hermes-zh-CN-Setup.exe "$SITE_WEB_DIR/Hermes-zh-CN-Setup.exe"
  cmp -s hermes-macos-installer.zip "$SITE_WEB_DIR/hermes-macos-installer.zip"
  python3 - "$VERSION" "$SITE_WEB_DIR" <<'PY'
import json
import sys
from pathlib import Path

version, site = sys.argv[1], Path(sys.argv[2])
latest = json.loads((site / "latest.json").read_text(encoding="utf-8"))
manifest = json.loads((site / "packages/0.16.x/zh-CN/manifest.json").read_text(encoding="utf-8"))
if latest["latest"] != version:
    raise SystemExit("site latest version mismatch")
if manifest["version"] != version:
    raise SystemExit("site manifest version mismatch")
if latest["packages"][0]["sha256"] != manifest["files"][0]["sha256"]:
    raise SystemExit("site package sha mismatch")
if f"v=20260612-exe-3" not in latest["install_windows_exe"]:
    raise SystemExit("windows cache marker missing")
if f"v=20260612-mac-1" not in latest["install_macos_zip"]:
    raise SystemExit("mac cache marker missing")
print("site files ok")
PY
fi

shasum -a 256 Hermes-zh-CN-Setup.exe hermes-macos-installer.zip
printf 'release verification passed: %s\n' "$VERSION"
