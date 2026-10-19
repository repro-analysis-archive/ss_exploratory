"""Stages of the X run, each a separate process started by the orchestrator (pinned CPUs, code-lock threads).

    python -m xplore.x_stage c0       --locked SNAP --out DIR [--step6-work DIR] [--placeholder]
    python -m xplore.x_stage x1       --locked SNAP --out DIR [--step5-dir DIR] [--placeholder] [--n-boot B]
    python -m xplore.x_stage x2feat   --locked SNAP --out DIR --placeholder
    python -m xplore.x_stage compare  --locked SNAP --out DIR --step6-work DIR --records DIR --meta FILE
                                      [--placeholder --cells LIST --max-reps M] [--n-boot B]
"""
import argparse
import json
import os
import sys

import numpy as np

from .common import C0_CELLS, C0_REPS, json_read, json_write, sha256_file, union_cells, use_locked


def _placeholder_full():
    from ss_benchmark import placeholder as ph
    rep_set, designs, reps, _, full = ph.build(set_names=("primary",))
    return rep_set, designs["primary"], reps["primary"], full


def stage_c0(a):
    from .x_units import control_c0, setup
    if a.placeholder:
        D, root, feats = setup(True, None)
    else:
        D, root, feats = setup(False, os.path.join(a.step5_dir, "reps.npz"))
    res = control_c0(D, root, feats, a.step6_work, C0_CELLS, C0_REPS)
    json_write(os.path.join(a.out, "c0.json"), res)
    print(f"control C0: {'passed' if res['passed'] else 'FAILED'}", flush=True)
    return 0 if res["passed"] else 4


def stage_x1(a):
    from ss_benchmark import checks

    from . import x1_checks, x1_erasure
    d = os.path.join(a.out, "x1")
    os.makedirs(d, exist_ok=True)
    keys = ("P", "S", "REF")
    if a.placeholder:
        rep_set, Dp, _, full = _placeholder_full()
        inp = x1_erasure.placeholder_inputs(rep_set, Dp)
        R_by_key = {k: full[k]["R"] for k in keys}
        lens = np.array([len(x) for x in R_by_key["P"][0]])
        rows = checks.e2_rows(inp["prim_idx"], lambda i, w=dict(zip(inp["prim_idx"], inp["prim_w"])):
                              x1_erasure.region_rows(w[i]), inp["switch"], lens)
        kb = {} if a.n_boot is None else dict(n_boot=a.n_boot)
        step5 = {k: {"E2_primary": checks.e2_auc(rows, R_by_key[k], inp["folds"], inp["sites"], f"primary:{k}", **kb),
                     "E3_site_primary": None} for k in keys}
        ids = np.asarray(Dp.ids)
    else:
        inp = x1_erasure.real_inputs()
        R_by_key = {k: x1_erasure.unpack_full(os.path.join(a.step5_dir, f"reps_full_{k}.npz"))[0] for k in keys}
        step5 = json.load(open(os.path.join(a.step5_dir, "checks.json")))
        ids = inp["prim_ids"]
    feats, full_x1, reports = x1_erasure.build_x1(R_by_key, inp)
    fpath = os.path.join(d, "x1_features.npz")
    np.savez(fpath + ".tmp.npz", **{f"primary/{k}": v for k, v in feats.items()}, **{"primary/ids": ids.astype("U16")})
    os.replace(fpath + ".tmp.npz", fpath)
    json_write(os.path.join(d, "x1_erasure_report.json"), dict(reports=reports, features_sha256=sha256_file(fpath)))
    print("X1 erasure written", flush=True)
    e3 = x1_checks.x1_checks(full_x1, inp, step5, n_boot=a.n_boot)
    json_write(os.path.join(d, "x1_e3.json"), e3)
    print("X1 E3 checks written", flush=True)
    return 0


def stage_x2feat(a):
    """PLACEHOLDER only: the original (protocol-LEACE) PLACEHOLDER features in the reps.npz layout."""
    _, Dp, reps, _ = _placeholder_full()
    p = os.path.join(a.out, "x2_placeholder_features.npz")
    np.savez(p + ".tmp.npz", **{f"primary/{k}": reps[k] for k in ("P-C", "S-C", "REF-C")},
             **{"primary/ids": np.asarray(Dp.ids).astype("U16")})
    os.replace(p + ".tmp.npz", p)
    return 0


def stage_compare(a):
    from ss_benchmark.constants import M_REPLICATES, N_BOOTSTRAP

    from . import x_compare
    from .common import ANALYSES, PLAN_GROUPS, cell_groups
    cells = [int(x) for x in a.cells.split(",")] if a.cells else union_cells()
    groups = cell_groups() if not a.cells else {g: [c for c in v if c in cells] for g, v in PLAN_GROUPS.items()}
    groups = {g: v for g, v in groups.items() if v}
    M = M_REPLICATES if a.max_reps is None else min(M_REPLICATES, a.max_reps)
    analyses = tuple(ANALYSES)
    x = x_compare.load_x(a.out, analyses, cells, M)
    s6 = x_compare.load_step6(a.step6_work, cells, M)
    pairing = x_compare.pairing_check(x, s6, analyses, cells, M)
    meta = json_read(a.meta, {})
    c0 = json_read(os.path.join(a.out, "c0.json"))
    er = json_read(os.path.join(a.out, "x1", "x1_erasure_report.json"))
    e3 = json_read(os.path.join(a.out, "x1", "x1_e3.json"))
    paths, rep = x_compare.write_records(a.records, a.out, meta, pairing, c0, er["reports"], e3, x, s6, analyses,
                                         groups, a.placeholder, a.n_boot or N_BOOTSTRAP)
    json_write(os.path.join(a.out, "compare_done.json"), dict(records={k: sha256_file(p) for k, p in paths.items()},
                                                            x_replicates=dict(path=rep, sha256=sha256_file(rep))))
    print(f"comparison written: {len(paths)} record files", flush=True)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("c0", "x1", "x2feat", "compare"))
    ap.add_argument("--locked", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--step5-dir")
    ap.add_argument("--step6-work")
    ap.add_argument("--records")
    ap.add_argument("--meta")
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("--cells")
    ap.add_argument("--max-reps", type=int)
    ap.add_argument("--n-boot", type=int)
    a = ap.parse_args(argv)
    use_locked(a.locked)
    return {"c0": stage_c0, "x1": stage_x1, "x2feat": stage_x2feat, "compare": stage_compare}[a.stage](a)


if __name__ == "__main__":
    sys.exit(main())
