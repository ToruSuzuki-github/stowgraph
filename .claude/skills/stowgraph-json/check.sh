#!/usr/bin/env bash
# Prerequisite check for the stowgraph-json skill. Called from "Current status" in SKILL.md.
# Claude Code blocks complex shell syntax written directly in SKILL.md at the permission check, so it is collected here.
# It can be run from anywhere: it locates the stowgraph folder from this file's position and checks there.
root="$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd -P)"
cd "$root" || exit 1

if command -v docker >/dev/null 2>&1 && docker version --format '{{.Server.Version}}' >/dev/null 2>&1; then
  echo "docker: available"
else
  echo "docker: unavailable"
fi

if [ -f generate.py ]; then
  echo "generate.py: present"
else
  echo "generate.py: missing"
fi

if [ -x .venv/bin/python ] && [ "$(.venv/bin/python -c 'import platform; print(platform.python_version())')" = "$(cat .python-version 2>/dev/null)" ]; then
  echo "venv: available"
else
  echo "venv: unavailable"
fi

echo "--- JSON files in repos/"
ls repos/*.json 2>/dev/null || echo "(none)"
