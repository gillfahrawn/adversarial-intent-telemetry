# data/gt_harmbench/ — GT-HarmBench

## What this is

GT-HarmBench is a dataset of scenario-framed 2x2 game matrices (Prisoner's
Dilemma, Chicken, Stag Hunt) used by `experiments/exp_f3_reciprocity.py` to
test the F3 payoff-perturbation mechanism as an analytical, mechanism-design
question: does the intervention shift the Nash equilibrium of each game
toward cooperation? This is not an evaluation of LLM behavior — the
mechanism is applied directly to the payoff matrices in the dataset, and
"cooperation" refers to the game-theoretic outcome, not a model's response.

**Not redistributed.** GT-HarmBench is hosted on HuggingFace as a gated
dataset (`gtfintechlab/GT-HarmBench`) and requires HuggingFace
authentication to access. It is excluded from git via `data/.gitignore`
(`*.csv`); only this documentation is tracked.

## What is expected on disk

```
data/gt_harmbench/GTHarmbenchdatatrain00000of00001.csv
```

`experiments/exp_f3_reciprocity.py` reads exactly this path
(`DATA_CSV = ROOT / "data/gt_harmbench/GTHarmbenchdatatrain00000of00001.csv"`)
and validates it against expected row/category counts (2009 rows; 654
Prisoner's Dilemma, 491 Chicken, 403 Stag Hunt; 1528 social-dilemma rows)
before running. If the file is missing, the script prints the HuggingFace
path and exits with a clear error rather than failing silently —
`scripts/reproduce_public.sh` checks for this file and skips the experiment
with the same message if it is absent.

## How to obtain it

The dataset is hosted at `https://huggingface.co/datasets/gtfintechlab/GT-HarmBench`.
Access requires HuggingFace authentication (the dataset is gated). After
access is granted:

```bash
huggingface-cli download gtfintechlab/GT-HarmBench \
  data/train-00000-of-00001.parquet --repo-type dataset
```

Convert the downloaded parquet file to CSV and place it at
`data/gt_harmbench/GTHarmbenchdatatrain00000of00001.csv`.

## Safety constraints

The dataset's `description`/`story_row`/`story_col` fields contain scenario
narratives for the game matrices; these are third-party dataset content, not
generated or redistributed by this repository. Do not quote or paraphrase
scenario text from this dataset into code, comments, commit messages, or
generated documentation — analysis in this repository reports only the
resulting numeric payoff matrices and defection/cooperation rates.
