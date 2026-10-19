"""X1 eraser (plan §1): LEACE fitted per fold on the analysis region of the 158-case primary set's training folds.

For each fold v of the fixed §2 split, the locked `reduce.fit_leace` (unchanged) is fitted on the fold-v PCA
coordinates (the protocol's 64 PCs from the 278-case PCA; the PCA is not refitted) of the analysis-region steps
(window-relative −30 … 44, §7.2; the rows E3 uses for the 158-case set) of the training-fold cases of the primary set
(fold ≠ v), with the one-hot centre as the concept. The eraser is applied to every case's fold-v coordinates (only the
158 primary cases are used downstream) and the window-step features (steps w_i … w_i + 14) form the X1 versions of
P−C, S−C and REF−C in the `primary/<key>-C` layout of the step-5 reps.npz: (5 folds, 158 cases, 15 steps, 64).

The same functions serve the real run (step-5 reps_full_<key>.npz) and the PLACEHOLDER tests (placeholder.build).
"""
import numpy as np

from ss_benchmark import reduce
from ss_benchmark.constants import ANALYSIS_REGION, N_FOLDS

K_MAX = 15


def unpack_full(path):
    """reps_full_<key>.npz -> (R, RC): per fold, a list of per-case arrays (the layout of pipeline._unpack_full;
    re-implemented here because importing ss_benchmark.pipeline loads torch)."""
    z = np.load(path, allow_pickle=False)
    lens = z["lengths"]
    cuts = np.cumsum(lens)[:-1]
    R = [np.split(z[f"R_{v}"], cuts) for v in range(N_FOLDS)]
    RC = [np.split(z[f"RC_{v}"], cuts) for v in range(N_FOLDS)] if "RC_0" in z.files else None
    return R, RC


def region_rows(w_i, region=ANALYSIS_REGION):
    lo, hi = region
    return np.arange(w_i + lo, w_i + hi + 1)


def fit_x1(R, sites, folds, prim_idx, prim_w, region=ANALYSIS_REGION):
    """R[v][i]: fold-v coordinates of case i (all representation-set cases); sites, folds: per case; prim_idx: the
    primary cases' indices into R; prim_w: their window starts. Returns (RC_X1, report) with RC_X1[v][i] for all
    cases."""
    sites, folds = np.asarray(sites), np.asarray(folds)
    prim_idx, prim_w = np.asarray(prim_idx), np.asarray(prim_w)
    n_folds = len(R)
    RC, report = [], []
    for v in range(n_folds):
        train = [(i, w) for i, w in zip(prim_idx, prim_w) if folds[i] != v]
        for i, w in train:
            rr = region_rows(w, region)
            if rr[0] < 0 or rr[-1] >= len(R[v][i]):
                raise ValueError(f"analysis region of case {i} outside its steps")
        X = np.concatenate([R[v][i][region_rows(w, region)] for i, w in train])
        z = np.concatenate([np.full(len(region_rows(w, region)), sites[i]) for i, w in train])
        le, _ = reduce.fit_leace(X, z)
        RC.append([le.transform(r) for r in R[v]])
        Xe = le.transform(X)
        report.append(dict(fold=v, n_fit_cases=len(train), n_fit_rows=int(len(X)), n_sites=int(len(np.unique(z))),
                           leace_rank=int(le.rank), leace_dim_retained=int(X.shape[1] - le.rank),
                           leace_var_retained=float(np.trace(np.cov(Xe.T)) / np.trace(np.cov(X.T))),
                           leace_identities=reduce.leace_identities(le, X, z)))
    return RC, report


def windowed(RC, prim_idx, prim_w, k_max=K_MAX):
    """(n_folds, n_primary, k_max, d): window steps w_i … w_i + k_max − 1 of every primary case under each fold's map
    (the layout of the step-5 reps.npz `primary/<key>-C`)."""
    return np.stack([np.stack([RC[v][i][w:w + k_max] for i, w in zip(prim_idx, prim_w)])
                     for v in range(len(RC))]).astype(np.float64)


def real_inputs():
    """Representation-set sites and folds, and the primary set's indices and window starts (locked design code)."""
    from ss_benchmark import design
    cases = design.representation_cases()
    folds = design.representation_folds().loc[cases.case_id].to_numpy()
    D = design.load_real_design("primary")
    pos = {cid: i for i, cid in enumerate(cases.case_id)}
    prim_idx = np.array([pos[c] for c in D.ids])
    return dict(sites=cases.center.to_numpy(), folds=folds, prim_idx=prim_idx, prim_w=D.window_start(),
                prim_ids=np.asarray(D.ids), switch=design.representation_switch_steps().loc[cases.case_id].to_numpy())


def placeholder_inputs(rep_set, design_primary):
    pos = {cid: i for i, cid in enumerate(rep_set.case_id)}
    prim_idx = np.array([pos[c] for c in design_primary.ids])
    return dict(sites=rep_set.centre.to_numpy(), folds=rep_set.fold.to_numpy(), prim_idx=prim_idx,
                prim_w=design_primary.window_start(), prim_ids=np.asarray(design_primary.ids),
                switch=rep_set.s.to_numpy())


def build_x1(R_by_key, inp):
    """{key: R} -> (features {"<key>-C": (5, 158, 15, 64)}, full {key: RC_X1}, reports {key: [...]})."""
    feats, full, reports = {}, {}, {}
    for key, R in R_by_key.items():
        RC, rep = fit_x1(R, inp["sites"], inp["folds"], inp["prim_idx"], inp["prim_w"])
        feats[f"{key}-C"] = windowed(RC, inp["prim_idx"], inp["prim_w"])
        full[key] = RC
        reports[key] = rep
    return feats, full, reports
