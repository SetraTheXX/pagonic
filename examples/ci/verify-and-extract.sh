#!/usr/bin/env bash
# Inspect and verify an archive before any extraction step.
set -euo pipefail

archive="${1:?Usage: $0 ARCHIVE [OUTPUT] [MAX_RISK]}"
output="${2:-extracted}"
max_risk="${3:-low}"

pagonic verify "$archive" --max-risk "$max_risk"
pagonic safe-extract "$archive" "$output" --allow-risk "$max_risk" --dry-run
pagonic safe-extract "$archive" "$output" --allow-risk "$max_risk"
