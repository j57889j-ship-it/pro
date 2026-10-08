#!/usr/bin/env bash
set -euo pipefail
python -m compileall -q app
pytest -q
echo "Verification complete."
