"""Wall-time estimate of the real X run (plan §8 method, calibrated on step 6's actual throughput).

Method (plan §8, as the code-lock projection): Σ over the 71 cells, the three arms and M = 200 replicates of the mean
measured wall time per SDR fit (code-lock PLACEHOLDER timing table, primary set, same K, W, arm and learner mode),
divided by the number of workers. Calibration: the code-lock projection for step 6 (no reductions; 20 workers) is
rescaled to 18 workers and compared with step 6's actual wall time (progress-log launch and completion); the ratio is
applied to the X projection.

    python -m xplore.x_estimate --locked SNAP --step6-log FILE
"""
import argparse
import datetime
import json
import os
import sys

import pandas as pd

from .common import ANALYSES, X_ARMS, union_cells, use_locked


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked", required=True)
    ap.add_argument("--step6-log", required=True)
    ap.add_argument("--workers", type=int, default=18)
    a = ap.parse_args(argv)
    use_locked(a.locked)
    from ss_benchmark import grid
    t = pd.read_csv(os.path.join(a.locked, "results/codelock_gate/projection_PLACEHOLDER_timings.csv"))
    t = t[t.set == "primary"]
    mean = t.groupby(["mode", "K", "W", "arm"]).wall_seconds.mean()
    cells = [grid.all_cells()[c] for c in union_cells()]
    fit_s = {an: sum(200 * mean[(mode, c.K, c.W, arm)] for c in cells for arm in X_ARMS)
             for an, mode in ANALYSES.items()}
    proj = json.load(open(os.path.join(a.locked, "results/codelock_gate/projection_PLACEHOLDER.json")))
    s6_proj_20 = proj["projection_steps"][0]["projected_wall_seconds"]
    s6_proj = s6_proj_20 * proj["n_workers"] / a.workers
    log = open(a.step6_log).read().splitlines()
    start = next(l for l in log if "grid: start (attempt 1)" in l)[:25]
    end = next(l for l in log if "step 6 complete" in l)[:25]
    actual = (datetime.datetime.fromisoformat(end) - datetime.datetime.fromisoformat(start)).total_seconds()
    ratio = actual / s6_proj
    out = dict(method=__doc__.split("\n\n")[1].replace("\n", " "), workers=a.workers,
               fit_seconds=fit_s, projected_hours={an: s / a.workers / 3600 for an, s in fit_s.items()},
               step6=dict(projected_wall_seconds_20_workers=s6_proj_20, projected_wall_seconds_18_workers=s6_proj,
                          actual_wall_seconds=actual, actual_start=start, actual_end=end, ratio_actual_to_projected=ratio),
               calibrated_hours={an: s / a.workers / 3600 * ratio for an, s in fit_s.items()})
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
