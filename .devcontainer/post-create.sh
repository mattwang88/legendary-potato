#!/usr/bin/env bash

set -euo pipefail

# Install uv if missing (matches the uv-based workflow in the other workspace repos).
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi
export PATH="$HOME/.local/bin:$PATH"

# Create .venv and install dependencies from pyproject.toml.
uv sync
