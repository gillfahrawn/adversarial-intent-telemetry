#!/usr/bin/env bash
#
# Reproduce the subset of experiments in this repository that do not require
# restricted or gated data (PAN 2012, GT-HarmBench). See README.md "Reproduce"
# and CLAUDE.md Sec. 3 for what each output file supports.
#
# Fails fast on missing Python dependencies. Skips (does not fail) experiments
# whose optional gated dataset is not present on disk, since that dataset
# cannot be shipped with this repository.
#
# Usage: bash scripts/reproduce_public.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON="${PYTHON:-python3}"

echo "== Checking dependencies =="
if ! "$PYTHON" -c "import numpy, matplotlib" >/dev/null 2>&1; then
    echo "ERROR: missing required Python packages (numpy, matplotlib)." >&2
    echo "Install with: pip install -r requirements.txt" >&2
    exit 1
fi
echo "numpy and matplotlib importable. Continuing."
echo

run() {
    local label="$1"
    local script="$2"
    echo "== Running: $label =="
    "$PYTHON" "$script"
    echo
}

run "Synthetic S-curve (illustrative, not real-data performance)" \
    "validation/synthetic/s_curve.py"

run "M8 Byzantine tolerance sweep (simulation)" \
    "experiments/exp_m8_byzantine.py"

run "M8 SPRT vs. Hoeffding isolation (simulation)" \
    "experiments/exp_m8_sprt.py"

GT_CSV="data/gt_harmbench/GTHarmbenchdatatrain00000of00001.csv"
if [ -f "$GT_CSV" ]; then
    run "F3 reciprocity mechanism (analytical, GT-HarmBench)" \
        "experiments/exp_f3_reciprocity.py"
else
    echo "== Skipping: F3 reciprocity mechanism (analytical, GT-HarmBench) =="
    echo "  GT-HarmBench is a gated HuggingFace dataset and is not redistributed"
    echo "  in this repository. Expected file not found: $GT_CSV"
    echo "  See data/gt_harmbench/README.md to obtain it, then re-run this script."
    echo
fi

echo "== Not run by this script (require the restricted PAN 2012 corpus) =="
echo "  experiments/exp_m3_author_split.py"
echo "  experiments/exp_m3_frontier.py"
echo "  experiments/exp_trajectory_lift.py"
echo "  experiments/exp_annotate_pan_manifest.py"
echo "  See data/pan12/README.md to obtain PAN 2012, then run these directly."
echo

echo "== Done. Outputs written to validation/synthetic/results/ and experiments/results/ =="
