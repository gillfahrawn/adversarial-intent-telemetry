# data/pan12/test/

Expected local (not redistributed) contents:

- `pan12-sexual-predator-identification-test-corpus-2012-05-17.xml` — the
  PAN 2012 SPI held-out test corpus released by the shared task.

No experiment script in this repository currently reads this file directly;
the "test" splits reported in `experiments/results/` are held-out partitions
of the training XML (see `data/pan12/README.md` and the docstrings of
`experiments/exp_m3_author_split.py` / `exp_trajectory_lift.py`). This file
is kept for anyone extending the experiments to evaluate against the
original PAN test release.

See `data/pan12/README.md` for provenance, redistribution status, how to
obtain this file, and safety constraints. This directory is excluded from
git by the root `.gitignore` (`data/pan12/`); only this note is tracked.
