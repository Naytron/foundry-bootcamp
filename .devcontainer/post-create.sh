#!/usr/bin/env bash
set -euo pipefail

install_args=(--system)

if [[ -n "${UV_FIND_LINKS:-}" ]]; then
  install_args+=(--no-index --find-links "$UV_FIND_LINKS")
fi

if [[ -n "${UV_INSECURE_HOST:-}" ]]; then
  install_args+=(--allow-insecure-host "$UV_INSECURE_HOST")
fi

sudo -H --preserve-env=UV_INDEX_URL,UV_FIND_LINKS,UV_INSECURE_HOST \
  uv pip install "${install_args[@]}" \
  pip==26.2.1 \
  setuptools==84.0.0 \
  gitpython==3.1.59 \
  -e ".[dev]"
