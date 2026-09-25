#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -m)" != "x86_64" ]]; then
  echo 'Official Waymo 1.6.7 wheels require Linux x86_64.' >&2
  exit 1
fi
# Keep bootstrap tooling and the Python environment local to this project.
# Ubuntu prerequisites: sudo apt install python3-venv libgomp1 libglib2.0-0
python3 -m venv .bootstrap
.bootstrap/bin/python -m pip install 'uv==0.8.22'
.bootstrap/bin/uv python install 3.10
.bootstrap/bin/uv venv --python 3.10 .venv-ubuntu
.bootstrap/bin/uv pip install --python .venv-ubuntu/bin/python -r requirements-linux.txt
.bootstrap/bin/uv pip check --python .venv-ubuntu/bin/python
.venv-ubuntu/bin/python scripts/check_environment.py --official
.bootstrap/bin/uv pip freeze --python .venv-ubuntu/bin/python > requirements-ubuntu-resolved.txt
echo 'Ready: source .venv-ubuntu/bin/activate && python -m jupyterlab --no-browser --ip=127.0.0.1'
