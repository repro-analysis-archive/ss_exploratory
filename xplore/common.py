"""Shared definitions for the exploratory analyses X1 / X2 (EXPLORATORY_PLAN_X1_X2.md, commit b6d1cf7).

The locked code (`ss_benchmark`) is imported from a `git archive` snapshot of the main repository's step-7 record
commit; callers put that snapshot first on sys.path (`use_locked`) before importing anything that needs it. Nothing
here changes locked code.
"""
import datetime
import hashlib
import json
import os
import sys

PLAN_COMMIT = "b6d1cf7893bff97cd17775f2c4807654ad545781"
MAIN_REPO = "/home/user/projects/medical_video_causal_gate"
STEP7_RECORD_COMMIT = "2880d736c75fbaaed8abbce233e82229b65e4c2f"
SDR_COMMIT = "af56777e0f52b5c350dd7ba557d55b2394cbd4bf"
SDR_EXEMPT = frozenset({"ss_benchmark/models/prim_caformer.py"})          # CODELOCK_CORRECTION_001 (extraction only)
STEP5_DIR = "/media/user/LaCie/medvideo_gate/ss_step4_5/step5"
STEP6_OUT = "/media/user/LaCie/medvideo_gate/ss_step6"
DEFAULT_OUT = "/media/user/LaCie/medvideo_gate/ss_exploratory_X"          # plan §7
SNAPSHOT_PATHS = ("ss_benchmark", "data_audit/lead/out/DS203_d8_cases.csv", "data_audit/lead/out/ss_window_offsets.csv",
                  "data_audit/lead/out/ss_window_offsets_perW.csv", "results/step5", "results/step6",
                  "results/step7/STEP7_RECORD.md", "results/step7/step7_manifest.json",
                  "results/codelock_gate/projection_PLACEHOLDER_timings.csv",
                  "results/codelock_gate/projection_PLACEHOLDER.json")

ANALYSES = {"X1": "select", "X2": "linear"}                                # learner mode per analysis (plan §1)
X_ARMS = ("FM-P-C", "FM-S-C", "REF-C")
KEY_OF = {"FM-P-C": "P", "FM-S-C": "S", "REF-C": "REF"}
SITE_RETAINED = {"FM-P-C": "FM-P", "FM-S-C": "FM-S", "REF-C": "REF"}       # step-6 FM-k comparator (plan §5)
COMPARATORS = ("minusC", "FM", "NV")                                       # step-6 k−C, step-6 FM-k, step-6 NV
C0_CELLS = (2, 18)                                                         # implementation note N8
C0_REPS = (0, 1)

PLAN_GROUPS = {   # plan §2, verbatim indices
    "P1b-FM": [*range(18, 24), *range(36, 42), *range(72, 78), *range(90, 96), *range(126, 132), *range(144, 150),
               *range(180, 186), *range(198, 204)],
    "P2-FM": [*range(2, 6), *range(8, 12), *range(14, 18)],
    "slice": [15, 33, 51, 69, 87, 105, 123, 141, 159, 177, 195, 213],
}
CODELOCK_ENV = dict(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1",
                    PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")


def use_locked(snapshot):
    """Put the locked-code snapshot first on sys.path and check that ss_benchmark is imported from it."""
    snapshot = os.path.abspath(snapshot)
    if snapshot not in sys.path:
        sys.path.insert(0, snapshot)
    import ss_benchmark
    got = os.path.dirname(os.path.dirname(os.path.abspath(ss_benchmark.__file__)))
    if got != snapshot:
        raise RuntimeError(f"ss_benchmark imported from {got}, not from the snapshot {snapshot}")
    return ss_benchmark


def cell_groups():
    """The plan's three groups, recomputed from the locked grid and checked against the plan's index lists."""
    from ss_benchmark import grid
    cells = grid.all_cells()
    calc = {"P1b-FM": [c.index for c in grid.family_cells("P1b-FM")],
            "P2-FM": [c.index for c in grid.family_cells("P2-FM")],
            "slice": [c.index for c in cells if c.phi == 0.0 and c.W == 30 and c.alpha == 0.5 and c.gamma == 1.0]}
    for g, idx in calc.items():
        if sorted(idx) != sorted(PLAN_GROUPS[g]):
            raise RuntimeError(f"group {g}: locked grid gives {idx}, plan lists {PLAN_GROUPS[g]}")
    return {g: sorted(v) for g, v in PLAN_GROUPS.items()}


def union_cells():
    u = sorted(set().union(*map(set, PLAN_GROUPS.values())))
    assert len(u) == 71, len(u)
    return u


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(p, bs=16 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(bs), b""):
            h.update(blk)
    return h.hexdigest()


def json_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=_jdefault)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _jdefault(x):
    import numpy as np
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    return str(x)


def json_read(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default
