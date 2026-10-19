"""Pairing, cell metrics, paired comparisons and the exploratory report for X1 / X2 (plan §3, §5, §6).

* Pairing check: every X record (cell, replicate) has its step-6 counterpart and the truths are identical (exact
  float equality); any mismatch or missing replicate stops the analysis.
* Cell metrics: the locked `grid.cell_metrics` per (analysis, cell, arm), with the extra fields of
  `grid_driver.aggregate` (support-failure rate, ESS, density-ratio range).
* Paired comparisons, for each X ∈ {X1, X2}, arm k−C and comparator B ∈ {step-6 k−C, step-6 FM-k, step-6 NV}:
  per cell Δ = (|bias_A| − |bias_B|) / mean truth (negative = the X arm has smaller |bias|) and the coverage
  difference cov_A − cov_B, with 95 % percentile intervals from a paired bootstrap of replicates within the cell (the
  same indices for both arms; B = 2,000); per group (P1b-FM, P2-FM, main slice) the mean Δ over the group's cells with
  the §12.3 scheme (one generator per comparison and group; for each cell in increasing index a (B, M) index matrix;
  cells fixed) and the number of cells with Δ < 0. Seeds: SeedSequence(20261008) named children
  "exploratory:<X>:<arm>:step6-<B arm>:<cell index | group>". No threshold, no verdict.
"""
import gzip
import json
import os

import numpy as np
import pandas as pd

from ss_benchmark import grid, seeds
from ss_benchmark.constants import N_BOOTSTRAP, SEED_BOOTSTRAP

from .common import ANALYSES, PLAN_COMMIT, SITE_RETAINED, X_ARMS

STEP6_ARMS = ("FM-P-C", "FM-S-C", "REF-C", "FM-P", "FM-S", "REF", "NV")
FIELDS = ("cell", "rep", "arm", "truth", "est", "se", "ci_lo", "ci_hi", "support_failure", "ess_min", "ratio_min",
          "ratio_max", "n_outcome_mlp", "n_ratio_mlp", "mode")


class PairingError(Exception):
    pass


def comparator_arm(arm, comp):
    return {"minusC": arm, "FM": SITE_RETAINED[arm], "NV": "NV"}[comp]


def load_shards(paths, keep_arms):
    rows = []
    for p in paths:
        for r in json.load(open(p)):
            if r["arm"] in keep_arms:
                rows.append({k: r.get(k) for k in FIELDS} | {"analysis": r.get("analysis")})
    return pd.DataFrame(rows)


def load_x(x_out, analyses, cells, M):
    paths = [os.path.join(x_out, "units", a, f"c{ci:03d}_r{r:04d}.json") for a in analyses for ci in cells
             for r in range(M)]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise PairingError(f"{len(missing)} X shards missing, e.g. {missing[:2]}")
    return load_shards(paths, set(X_ARMS))


def load_step6(work_primary, cells, M):
    paths = [os.path.join(work_primary, f"c{ci:03d}_r{r:04d}.json") for ci in cells for r in range(M)]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise PairingError(f"{len(missing)} step-6 shards missing, e.g. {missing[:2]}")
    return load_shards(paths, set(STEP6_ARMS))


def pairing_check(x, s6, analyses, cells, M):
    """Every (analysis, cell, replicate) of X has all three arms, one truth equal across them, and its step-6
    counterpart (all comparator arms present) with an identical truth."""
    want = {(ci, r) for ci in cells for r in range(M)}
    t6 = s6.groupby(["cell", "rep"]).truth.agg(["min", "max", "count"])
    if set(t6.index) != want or (t6["min"] != t6["max"]).any() or (t6["count"] != len(STEP6_ARMS)).any():
        raise PairingError("step-6 records incomplete or with inconsistent truths across arms")
    n = 0
    for a in analyses:
        xa = x[x.analysis == a]
        tx = xa.groupby(["cell", "rep"]).truth.agg(["min", "max", "count"])
        if set(tx.index) != want or (tx["min"] != tx["max"]).any() or (tx["count"] != len(X_ARMS)).any():
            raise PairingError(f"{a}: records incomplete or with inconsistent truths across arms")
        j = tx[["min"]].join(t6[["min"]], lsuffix="_x", rsuffix="_6")
        bad = j[j.min_x.to_numpy() != j.min_6.to_numpy()]
        if len(bad):
            raise PairingError(f"{a}: truth differs from step 6 in {len(bad)} (cell, replicate) pairs, e.g. "
                               f"{list(bad.index[:3])}")
        n += len(j)
    return dict(passed=True, pairs_checked=n, cells=len(cells), replicates_per_cell=M)


def x_cell_metrics(x):
    rows = []
    for (a, ci, arm), g in x.groupby(["analysis", "cell", "arm"], sort=True):
        g = g.sort_values("rep")
        m = grid.cell_metrics(g.est, g.se, g.ci_lo, g.ci_hi, g.truth)
        rows.append(dict(analysis=a, cell=int(ci), arm=arm, mode=ANALYSES[a], **grid.all_cells()[int(ci)].as_dict(),
                         **m, support_failure_rate=float(g.support_failure.astype(float).mean()),
                         ess_min=float(g.ess_min.min()), ratio_min=float(g.ratio_min.min()),
                         ratio_max=float(g.ratio_max.max()), outcome_mlp_fits=int(g.n_outcome_mlp.sum()),
                         ratio_mlp_fits=int(g.n_ratio_mlp.sum())))
    return pd.DataFrame(rows)


def _cov(df):
    est, se, lo, hi, tr = (df[c].to_numpy(float) for c in ("est", "se", "ci_lo", "ci_hi", "truth"))
    return ((lo <= tr) & (tr <= hi) & np.isfinite(est) & np.isfinite(se)).astype(float)


def _delta(eA, eB, tr):
    """Δ for arrays whose last axis is the replicate axis."""
    return (np.abs((eA - tr).mean(-1)) - np.abs((eB - tr).mean(-1))) / tr.mean(-1)


def paired_arrays(xa, s6, ci, arm, comp):
    A = xa[(xa.cell == ci) & (xa.arm == arm)].sort_values("rep")
    B = s6[(s6.cell == ci) & (s6.arm == comparator_arm(arm, comp))].sort_values("rep")
    assert (A.rep.to_numpy() == B.rep.to_numpy()).all()
    eA, eB, tr = A.est.to_numpy(float), B.est.to_numpy(float), A.truth.to_numpy(float)
    cA, cB = _cov(A), _cov(B)
    ok = np.isfinite(eA) & np.isfinite(eB) & np.isfinite(tr)
    return eA[ok], eB[ok], tr[ok], cA[ok], cB[ok], int((~ok).sum())


def seed_name(a, arm, comp, where):
    return f"exploratory:{a}:{arm}:step6-{comparator_arm(arm, comp)}:{where}"


def compare(x, s6, analyses, groups, n_boot=N_BOOTSTRAP):
    root = np.random.SeedSequence(SEED_BOOTSTRAP)
    cells_rows, group_rows = [], []
    for a in analyses:
        xa = x[x.analysis == a]
        for arm in X_ARMS:
            for comp in ("minusC", "FM", "NV"):
                cache = {}
                for ci in sorted(set().union(*map(set, groups.values()))):
                    eA, eB, tr, cA, cB, dropped = paired_arrays(xa, s6, ci, arm, comp)
                    M = len(tr)
                    rng = seeds.rng(root, seed_name(a, arm, comp, ci))
                    b = rng.integers(0, M, size=(n_boot, M))
                    d_star = _delta(eA[b], eB[b], tr[b])
                    c_star = cA[b].mean(1) - cB[b].mean(1)
                    d = float(_delta(eA, eB, tr))
                    cache[ci] = (eA, eB, tr)
                    cells_rows.append(dict(
                        analysis=a, arm=arm, comparator=f"step6 {comparator_arm(arm, comp)}", comparison=comp,
                        cell=ci, **{k: v for k, v in grid.all_cells()[ci].as_dict().items() if k != "index"},
                        groups=",".join(g for g, idx in groups.items() if ci in idx), M=M, dropped_nonfinite=dropped,
                        mean_truth=float(tr.mean()), abs_bias_A=float(abs((eA - tr).mean())),
                        abs_bias_B=float(abs((eB - tr).mean())), delta=d,
                        delta_lo=float(np.percentile(d_star, 2.5)), delta_hi=float(np.percentile(d_star, 97.5)),
                        cov_A=float(cA.mean()), cov_B=float(cB.mean()), cov_diff=float(cA.mean() - cB.mean()),
                        cov_diff_lo=float(np.percentile(c_star, 2.5)), cov_diff_hi=float(np.percentile(c_star, 97.5)),
                        seed_name=seed_name(a, arm, comp, ci)))
                for g, idx in groups.items():
                    rng = seeds.rng(root, seed_name(a, arm, comp, g))
                    boot = np.zeros(n_boot)
                    pts = []
                    for ci in sorted(idx):
                        eA, eB, tr = cache[ci]
                        M = len(tr)
                        b = rng.integers(0, M, size=(n_boot, M))
                        boot += _delta(eA[b], eB[b], tr[b])
                        pts.append(float(_delta(eA, eB, tr)))
                    boot /= len(idx)
                    group_rows.append(dict(analysis=a, arm=arm, comparator=f"step6 {comparator_arm(arm, comp)}",
                                           comparison=comp, group=g, n_cells=len(idx),
                                           mean_delta=float(np.mean(pts)),
                                           mean_delta_lo=float(np.percentile(boot, 2.5)),
                                           mean_delta_hi=float(np.percentile(boot, 97.5)),
                                           n_cells_delta_negative=int(sum(p < 0 for p in pts)),
                                           seed_name=seed_name(a, arm, comp, g)))
    return pd.DataFrame(cells_rows), pd.DataFrame(group_rows)


# --------------------------------------------------------------------------------------------------- report --
BANNED = ("SUPPORTED", "CONTRADICTED", "consistent with the theory-motivated direction", "eliminated",
          "equivalent to chance")


def _f(x, nd=3):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{nd}f}"


def e3_lines(e3, boundary=0.35):
    L = ["| key | linear BA | linear one-sided 95 % upper | MLP BA | MLP one-sided 95 % upper | E3-state (X1) | "
         "step-5 linear upper (protocol LEACE) |", "|---|---:|---:|---:|---:|---|---:|"]
    words = []
    for key, r in e3.items():
        s = r["E3_site_primary_X1"]
        st = r["E3_state_primary_X1"]
        st_txt = (f"retained fraction {_f(st['retained_fraction'])}" if st.get("applicable")
                  else "not applicable (E2 primary failed at step 5)")
        ref = (r.get("step5_reference") or {}).get("E3_site_primary") or {}
        L.append(f"| {key} | {_f(s['linear']['ba'])} | {_f(s['linear']['upper_one_sided_95'])} | {_f(s['mlp']['ba'])} "
                 f"| {_f(s['mlp']['upper_one_sided_95'])} | {st_txt} | "
                 f"{_f((ref.get('linear') or {}).get('upper_one_sided_95'))} |")
        lin = s["linear"]["upper_one_sided_95"] <= boundary
        mlp = s["mlp"]["upper_one_sided_95"] <= boundary
        words.append(f"* {key}: after the X1 erasure, linear site information "
                     + ("no longer exceeds the prespecified linear site-encoding boundary" if lin else
                        "still exceeds the prespecified linear site-encoding boundary")
                     + f" ({boundary}); the MLP probe's one-sided upper bound "
                     + ("does not exceed" if mlp else "exceeds") + " the same boundary.")
    return L + [""] + words


def report(meta, pairing, c0, erasure, e3, metrics, cells_df, groups_df, placeholder):
    L = [("# PLACEHOLDER — " if placeholder else "# ") + "Exploratory analyses X1 / X2 (outside the frozen protocol)", ""]
    if placeholder:
        L += ["> **PLACEHOLDER — synthetic test output, not results.**", ""]
    L += [f"* **Plan:** `EXPLORATORY_PLAN_X1_X2.md`, commit `{PLAN_COMMIT}` (OSF https://osf.io/5c627, embargoed).",
          "* **Status:** exploratory. No family verdict is produced and no §12 / §13 result is altered: P1b-FM and "
          "P2-FM remain not tested (§13); FM vs FM−C comparisons in the protocol grid remain descriptive only.",
          "* **Reading:** in this exploratory analysis, Δ = (|bias_A| − |bias_B|) / mean truth, with A the X arm and B "
          "the step-6 comparator; negative Δ means the X arm had the smaller |bias|. Intervals are 95 % paired "
          "bootstrap percentile intervals (B = 2,000). All 71 cells and all arms are reported.",
          f"* **Code:** `{meta.get('x_commit', 'n/a')}`; locked code snapshot of `{meta.get('locked_commit', 'n/a')}`.",
          ""]
    L += ["## Inputs", ""] + [f"* `{k}`: `{v}`" for k, v in sorted((meta.get("inputs") or {}).items())] + [""]
    L += ["## Pairing check and control C0", "",
          f"* Pairing check: {pairing['pairs_checked']} (analysis, cell, replicate) truths identical to step 6.",
          f"* Control C0 (original step-5 FM-P−C features, mode \"select\", cells / replicates "
          f"{[(u['cell'], u['rep']) for u in c0['units']]}): "
          + ("identical to the step-6 records in every field." if c0["passed"] else "NOT identical."), ""]
    L += ["## X1 erasure (per fold)", "", "| key | fold | fit cases | fit rows | rank | max identity residual | "
          "variance retained |", "|---|---:|---:|---:|---:|---:|---:|"]
    for key, folds in erasure.items():
        for f in folds:
            L.append(f"| {key} | {f['fold']} | {f['n_fit_cases']} | {f['n_fit_rows']} | {f['leace_rank']} | "
                     f"{max(f['leace_identities'].values()):.2e} | {_f(f['leace_var_retained'])} |")
    L += ["", "## E3 on the X1 erasure (158-case analysis region)", "",
          "The X1 eraser is fitted on training folds and evaluated on held-out folds of the same population; linear "
          "E3-site is expected near chance by construction (a check of the procedure). These results do not gate X1.",
          ""] + e3_lines(e3) + [""]
    L += ["## Group summaries (descriptive; no threshold)", "",
          "| analysis | arm | comparator | group | cells | mean Δ | 95 % interval | cells with Δ < 0 |",
          "|---|---|---|---|---:|---:|---|---:|"]
    for _, r in groups_df.iterrows():
        L.append(f"| {r.analysis} | {r.arm} | {r.comparator} | {r.group} | {r.n_cells} | {_f(r.mean_delta)} | "
                 f"[{_f(r.mean_delta_lo)}, {_f(r.mean_delta_hi)}] | {r.n_cells_delta_negative} |")
    L += ["", "## Per cell: X-arm metrics and paired comparisons (all 71 cells)", ""]
    for (a, arm), sub in cells_df.groupby(["analysis", "arm"], sort=True):
        m = metrics[(metrics.analysis == a) & (metrics.arm == arm)].set_index("cell")
        L += [f"**{a} ({ANALYSES[a]}): {arm}**", "",
              "| cell | K | P | W | α | γ | groups | rel. bias | coverage | Δ vs step6 k−C [95 %] | Δ vs step6 FM-k "
              "[95 %] | Δ vs step6 NV [95 %] | cov diff vs k−C [95 %] |",
              "|---:|---:|---:|---:|---:|---:|---|---:|---:|---|---|---|---|"]
        piv = {c: sub[sub.comparison == c].set_index("cell") for c in ("minusC", "FM", "NV")}
        for ci in sorted(sub.cell.unique()):
            r = piv["minusC"].loc[ci]
            cell = lambda c: f"{_f(piv[c].loc[ci].delta)} [{_f(piv[c].loc[ci].delta_lo)}, {_f(piv[c].loc[ci].delta_hi)}]"
            L.append(f"| {ci} | {r.K} | {r.P} | {r.W} | {r.alpha:g} | {r.gamma:g} | {r.groups} | "
                     f"{_f(m.loc[ci].rel_bias)} | {_f(m.loc[ci].coverage)} | {cell('minusC')} | {cell('FM')} | "
                     f"{cell('NV')} | {_f(r.cov_diff)} [{_f(r.cov_diff_lo)}, {_f(r.cov_diff_hi)}] |")
        L.append("")
    L += ["## Figures", "", "`X_heatmaps.pdf`: Δ and the coverage difference for every cell, arm and comparator.", ""]
    text = "\n".join(L) + "\n"
    for w in BANNED:
        assert w not in text, f"wording rule: {w!r} must not appear in the exploratory report"
    return text


def heatmaps(cells_df, path, placeholder):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 7})
    with PdfPages(path) as pdf:
        for a in sorted(cells_df.analysis.unique()):
            for comp in ("minusC", "FM", "NV"):
                for val, lab in (("delta", "Δ = (|bias_A| − |bias_B|) / mean truth"),
                                 ("cov_diff", "coverage difference cov_A − cov_B")):
                    sub = cells_df[(cells_df.analysis == a) & (cells_df.comparison == comp)]
                    cells = sorted(sub.cell.unique())
                    M = np.array([[sub[(sub.arm == arm) & (sub.cell == c)][val].iloc[0] for c in cells]
                                  for arm in X_ARMS])
                    lim = float(np.nanmax(np.abs(M))) or 1.0
                    fig, ax = plt.subplots(figsize=(11, 2.4))
                    im = ax.imshow(M, cmap="RdBu_r", vmin=-lim, vmax=lim, aspect="auto")
                    ax.set_yticks(range(len(X_ARMS)), X_ARMS)
                    ax.set_xticks(range(len(cells)), [str(c) for c in cells], rotation=90, fontsize=5)
                    ax.set_xlabel("cell index (all 71 cells)")
                    comp_lab = {"minusC": "step-6 k−C", "FM": "step-6 FM-k", "NV": "step-6 NV"}[comp]
                    ax.set_title(f"{'PLACEHOLDER — ' if placeholder else ''}{a} ({ANALYSES[a]}) vs {comp_lab}: {lab}")
                    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
                    fig.tight_layout()
                    pdf.savefig(fig)
                    plt.close(fig)


def write_records(rec_dir, x_out, meta, pairing, c0, erasure, e3, x, s6, analyses, groups, placeholder,
                  n_boot=N_BOOTSTRAP):
    """Compute everything and write the record files; returns their paths. X replicate rows go to x_out (gzip)."""
    os.makedirs(rec_dir, exist_ok=True)
    metrics = x_cell_metrics(x)
    cells_df, groups_df = compare(x, s6, analyses, groups, n_boot)
    rep_path = os.path.join(x_out, "x_replicates.csv.gz")
    with gzip.open(rep_path, "wt") as fh:
        x.sort_values(["analysis", "cell", "arm", "rep"]).to_csv(fh, index=False)
    paths = {}

    def put(name, write):
        p = os.path.join(rec_dir, name)
        write(p)
        paths[name] = p

    put("x_cell_metrics.csv", lambda p: metrics.to_csv(p, index=False))
    put("x_comparisons_cells.csv", lambda p: cells_df.to_csv(p, index=False))
    put("x_comparisons_groups.csv", lambda p: groups_df.to_csv(p, index=False))
    put("x_pairing_c0.json", lambda p: json.dump(dict(pairing=pairing, control_c0=c0), open(p, "w"), indent=1,
                                                 sort_keys=True))
    put("x1_erasure_report.json", lambda p: json.dump(erasure, open(p, "w"), indent=1, sort_keys=True, default=float))
    put("x1_e3.json", lambda p: json.dump(e3, open(p, "w"), indent=1, sort_keys=True, default=float))
    put("X_REPORT.md", lambda p: open(p, "w").write(report(meta, pairing, c0, erasure, e3, metrics, cells_df,
                                                           groups_df, placeholder)))
    put("X_heatmaps.pdf", lambda p: heatmaps(cells_df, p, placeholder))
    return paths, rep_path
