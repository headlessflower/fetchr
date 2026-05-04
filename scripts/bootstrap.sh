#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv --system-site-packages
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e .
echo
echo "Done."
echo "Activate with: source .venv/bin/activate"
