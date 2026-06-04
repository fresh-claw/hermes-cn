#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${XIAOMA_HERMES_BASE_URL:-https://useai.live/hermes}"
BASE_URL="${BASE_URL%/}"
export XIAOMA_HERMES_ENTRYPOINT="github-bash"

curl -fsSL "$BASE_URL/install.sh" | bash
