#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

chmod +x "$repo_root/.githooks/pre-commit" "$repo_root/.githooks/pre-push"
git -C "$repo_root" config core.hooksPath .githooks

echo "Git hooks enabled (core.hooksPath=.githooks)."
