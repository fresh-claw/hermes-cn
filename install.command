#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${XIAOMA_HERMES_BASE_URL:-https://useai.live/hermes}"
BASE_URL="${BASE_URL%/}"
export XIAOMA_HERMES_ENTRYPOINT="github-macos-command"

curl -fsSL "$BASE_URL/install.sh" | bash
printf '%s\n' ""
printf '%s\n' "Hermes 中文增强已完成。可以关闭此窗口。"
