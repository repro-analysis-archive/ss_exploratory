"""X unit runner (plan §3, §7): one unit = (analysis, cell, replicate); one shard per unit; resumable.

Each unit repeats exactly the locked `grid_driver._unit` steps for the primary set with the step-6 replicate seed:
    seq = seeds.replicate_seq(cell, replicate, root); d = dgp.draw; A, Y = dgp.simulate; truth = dgp.truth;
    X = arms.arm_covariates(arm, D, cell, d, reps); sdr.sdr_mtp(A, Y, X, W, K, D.folds, seeds.child(seq, "learners"),
    mode)
for the three arms FM-P−C, FM-S−C and REF−C. Only the features (X1: the X1 erasure; X2: the original step-5 LEACE
features) and the learner mode (X1: "select"; X2: "linear") differ from step 6. Records carry the grid_driver fields
plus "analysis". Workers: a fork pool (code-lock thread settings come from the environment set by the orchestrator).

    python -m xplore.x_units --locked SNAP --analysis X1|X2 --features FILE --out DIR --workers N
        [--placeholder] [--cells LIST] [--max-reps M]
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

_S = {}


def shard_path(out, analysis, ci, r):
    return os.path.join(out, "units", analysis, f"c{ci:03d}_r{r:04d}.json")


def unit_records(D, cell, r, root, reps, arm_list, mode, analysis):
    """The locked _unit computation for one (cell, replicate) and the given arms; returns the records."""
    from ss_benchmark import arms as arms_mod
    from ss_benchmark import dgp, sdr, seeds
    seq = seeds.replicate_seq(cell.index, r, root)
    d = dgp.draw(D, cell, seq)
    A, Y = dgp.simulate(D, cell, d)
    truth = dgp.truth(D, cell, d)
    recs = []
    for arm in arm_list:
        X = arms_mod.arm_covariates(arm, D, cell, d, reps)
        e = sdr.sdr_mtp(A, Y, X, cell.W, cell.K, D.folds, seeds.child(seq, "learners"), mode)
        rec = dict(set="primary", design=D.label, cell=cell.index, rep=r, arm=arm, mode=mode, truth=truth,
                   covered=bool(e["ci_lo"] <= truth <= e["ci_hi"]), **e)
        if analysis is not None:
            rec["analysis"] = analysis
        recs.append(rec)
    return recs


def _unit(args):
    out, analysis, ci, r = args
    path = shard_path(out, analysis, ci, r)
    if os.path.exists(path):
        return path
    from ss_benchmark import grid
    from .common import ANALYSES, X_ARMS
    recs = unit_records(_S["design"], grid.all_cells()[ci], r, _S["root"], _S["reps"], X_ARMS, ANALYSES[analysis],
                        analysis)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(recs, f, sort_keys=True)
    os.replace(tmp, path)
    return path


def load_features(path):
    """{"P-C": ..., "S-C": ..., "REF-C": ...} from an X1 features file or the step-5 reps.npz (`primary/<key>-C`)."""
    z = np.load(path, allow_pickle=False)
    out = {}
    for k in ("P-C", "S-C", "REF-C"):
        name = f"primary/{k}" if f"primary/{k}" in z.files else k
        out[k] = z[name]
    ids = z["primary/ids"] if "primary/ids" in z.files else (z["ids"] if "ids" in z.files else None)
    return out, ids


def setup(placeholder, features=None):
    """Design, replicate root and features; PLACEHOLDER: locked placeholder.build() and the grid_driver PLACEHOLDER
    root; real: the locked real primary design and root 20261007."""
    from ss_benchmark import design as design_mod
    from ss_benchmark import placeholder as ph
    from ss_benchmark import seeds
    from ss_benchmark.constants import SEED_REPLICATES
    if placeholder:
        _, designs, reps, _, _ = ph.build(set_names=("primary",))
        D = designs["primary"]
        root = int(seeds.placeholder_seq("grid-driver", "replicates").generate_state(1)[0])
        default = {k: reps["primary"][k] for k in ("P-C", "S-C", "REF-C")}
    else:
        D = design_mod.load_real_design("primary")
        root = SEED_REPLICATES
        default = None
    if features is not None:
        feats, ids = load_features(features)
        if ids is not None and list(ids) != list(D.ids):
            raise RuntimeError("feature case order differs from the primary design")
    else:
        feats = default
    for k, a in feats.items():
        if a.shape[1] != D.n:
            raise RuntimeError(f"features {k}: {a.shape} do not match {D.n} primary cases")
    return D, root, feats


def plan_units(analysis, cells, max_reps=None):
    from ss_benchmark.constants import M_REPLICATES
    M = M_REPLICATES if max_reps is None else min(M_REPLICATES, max_reps)
    return [(analysis, ci, r) for ci in cells for r in range(M)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked", required=True)
    ap.add_argument("--analysis", required=True, choices=("X1", "X2"))
    ap.add_argument("--features", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, required=True)
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("--cells")
    ap.add_argument("--max-reps", type=int)
    a = ap.parse_args(argv)
    from .common import union_cells, use_locked
    use_locked(a.locked)
    D, root, feats = setup(a.placeholder, a.features)
    _S.update(design=D, root=root, reps=feats)
    cells = [int(x) for x in a.cells.split(",")] if a.cells else union_cells()
    units = plan_units(a.analysis, cells, a.max_reps)
    os.makedirs(os.path.join(a.out, "units", a.analysis), exist_ok=True)
    todo = [u for u in units if not os.path.exists(shard_path(a.out, *u))]
    print(f"{time.strftime('%F %T')} {a.analysis}: {len(units)} units, {len(units) - len(todo)} present, "
          f"{len(todo)} to run on {a.workers} workers", flush=True)
    t0 = time.time()
    with mp.get_context("fork").Pool(a.workers) as pool:
        for k, _ in enumerate(pool.imap_unordered(_unit, [(a.out, *u) for u in todo], chunksize=1)):
            if (k + 1) % max(1, len(todo) // 100) == 0 or k + 1 == len(todo):
                print(f"{time.strftime('%F %T')} {a.analysis}: {k + 1}/{len(todo)} units; elapsed "
                      f"{time.time() - t0:.0f} s", flush=True)
    return 0


def control_c0(D, root, feats_original, step6_work_primary, cells, reps):
    """Plan §3 control C0: the X code path with the original step-5 features and mode "select" must reproduce the
    step-6 FM-P−C records bit for bit (every field of the step-6 record, after a JSON round trip)."""
    from ss_benchmark import grid
    rows = []
    for ci in cells:
        for r in reps:
            mine = unit_records(D, grid.all_cells()[ci], r, root, feats_original, ("FM-P-C",), "select", None)[0]
            mine = json.loads(json.dumps(mine, sort_keys=True))
            ref = [x for x in json.load(open(os.path.join(step6_work_primary, f"c{ci:03d}_r{r:04d}.json")))
                   if x["arm"] == "FM-P-C"]
            same = (lambda k: json.dumps(mine.get(k)) == json.dumps(ref[0][k]))         # NaN-safe exact comparison
            ok = len(ref) == 1 and set(mine) == set(ref[0]) and all(same(k) for k in ref[0])
            diff = [] if not ref else sorted(k for k in ref[0] if not same(k))
            rows.append(dict(cell=ci, rep=r, identical=bool(ok), fields_compared=len(ref[0]) if ref else 0,
                             differing_fields=diff))
    return dict(passed=all(x["identical"] for x in rows), units=rows)


if __name__ == "__main__":
    sys.exit(main())
