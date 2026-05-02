#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.bun/bin:$PATH"

ARCHON_SRC_DIR="/home/ubuntu/Archon"
if [[ ! -d "$ARCHON_SRC_DIR" ]]; then
  echo "archon source directory missing: $ARCHON_SRC_DIR" >&2
  exit 1
fi

cd "$ARCHON_SRC_DIR"
exec bun run cli "$@"
