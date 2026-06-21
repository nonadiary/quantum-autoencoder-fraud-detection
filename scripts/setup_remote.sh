#!/usr/bin/env bash
# Set up a fresh Ubuntu (22.04/24.04) CPU box to run the 8-method study.
# Usage:  bash scripts/setup_remote.sh
# Then:   . .venv/bin/activate && python src/run_experiments.py
set -euo pipefail

cd "$(dirname "$0")/.."   # repo root

echo "==> Installing Python 3.12 + venv (needs sudo)"
sudo apt-get update -y
sudo apt-get install -y python3.12 python3.12-venv python3-pip

echo "==> Creating virtualenv .venv"
python3.12 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip

echo "==> Installing pinned dependencies (this pulls TensorFlow + PennyLane; a few minutes)"
pip install -r requirements-run.txt

echo "==> Sanity check"
python - <<'PY'
import numpy, tensorflow, keras, pennylane, sklearn, pandas, scipy
print("numpy", numpy.__version__, "| tf", tensorflow.__version__,
      "| keras", keras.__version__, "| pennylane", pennylane.__version__)
import pennylane as qml
dev = qml.device("lightning.qubit", wires=4)   # confirm the fast CPU backend loads
print("lightning.qubit OK; CPU cores:", __import__("os").cpu_count())
PY

cat <<'EOF'

✅ Setup complete. To run the full study (use tmux/nohup so it survives SSH drop):

    . .venv/bin/activate
    nohup python src/run_experiments.py > run.log 2>&1 &
    tail -f run.log

Results are written to results/experiment_results_parallel_<timestamp>.json
EOF
