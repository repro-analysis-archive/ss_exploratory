"""PLACEHOLDER tests of the X1 / X2 components (criteria T1-T7 in X_IMPLEMENTATION_NOTES.md, fixed before running).

    taskset -c 18,19 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0 \
        /home/user/miniconda3/bin/python3 -m pytest -p no:cacheprovider -v tests/test_x_components.py
"""
import json

import numpy as np
import pandas as pd
import pytest

from conftest import locked_step6_shards
from xplore import common as C

TOL = 1e-8


# ----------------------------------------------------------------------------------------------- T1: X1 eraser --
def test_t1_x1_eraser_rows_rank_identities_shape(x1, inp):
    feats, _, reports = x1
    for key in ("P", "S", "REF"):
        assert feats[f"{key}-C"].shape == (5, 158, 15, 64)
        for f in reports[key]:
            n_train = int(sum(inp["folds"][i] != f["fold"] for i in inp["prim_idx"]))
            assert f["n_fit_rows"] == 75 * n_train and f["n_fit_cases"] == n_train
            assert f["leace_rank"] == 3
            assert max(f["leace_identities"].values()) <= TOL, f["leace_identities"]


def test_t1_x1_eraser_uses_only_primary_training_rows(ph, inp):
    from xplore import x1_erasure
    R = [list(r) for r in ph["full"]["P"]["R"]]
    v = 0
    nonprim = next(i for i in range(len(R[v])) if i not in set(inp["prim_idx"]))
    prim_heldout = next(i for i in inp["prim_idx"] if inp["folds"][i] == v)
    probe = next(i for i in inp["prim_idx"] if inp["folds"][i] != v)
    base, _ = x1_erasure.fit_x1([R[v]], inp["sites"], np.where(inp["folds"] == v, 0, 1), inp["prim_idx"], inp["prim_w"])
    R2 = [x.copy() for x in R[v]]
    R2[nonprim] = R2[nonprim] + 5.0
    R2[prim_heldout] = R2[prim_heldout] * 3.0
    alt, _ = x1_erasure.fit_x1([R2], inp["sites"], np.where(inp["folds"] == v, 0, 1), inp["prim_idx"], inp["prim_w"])
    assert np.array_equal(base[0][probe], alt[0][probe])          # same eraser: held-out / non-primary rows not used
    R3 = [x.copy() for x in R[v]]
    R3[probe] = R3[probe] * 1.01
    alt3, _ = x1_erasure.fit_x1([R3], inp["sites"], np.where(inp["folds"] == v, 0, 1), inp["prim_idx"], inp["prim_w"])
    assert not np.array_equal(base[0][nonprim], alt3[0][nonprim])  # a primary training row does change it


def test_t1_x1_differs_from_protocol_eraser(x1, ph):
    feats, _, _ = x1
    for k in ("P-C", "S-C", "REF-C"):
        assert not np.allclose(feats[k], ph["orig"][k])


def test_t1_unpack_full_roundtrip(ph, tmp_path):
    from xplore import x1_erasure
    f = ph["full"]["P"]
    lens = np.array([len(x) for x in f["R"][0]])
    p = tmp_path / "reps_full_P.npz"
    np.savez(p, lengths=lens, **{f"R_{v}": np.concatenate(f["R"][v]) for v in range(5)},
             **{f"RC_{v}": np.concatenate(f["R-C"][v]) for v in range(5)})
    R, RC = x1_erasure.unpack_full(str(p))
    for v in range(5):
        assert all(np.array_equal(a, b) for a, b in zip(R[v], f["R"][v]))
        assert all(np.array_equal(a, b) for a, b in zip(RC[v], f["R-C"][v]))


# ---------------------------------------------------------------------------------------------- T2: X1 E3 checks --
def test_t2_x1_e3_matches_locked_call(x1, inp):
    from ss_benchmark import checks
    from xplore import x1_checks, x1_erasure
    _, full, _ = x1
    ref = {"P": {"E2_primary": {"pass": True, "delta_auc": 0.1}}}
    out = x1_checks.x1_checks({"P": full["P"]}, inp, ref, n_boot=200)["P"]
    w = dict(zip(inp["prim_idx"], inp["prim_w"]))
    direct = checks.e3_site(full["P"], inp["prim_idx"], inp["sites"], inp["folds"],
                            lambda i: x1_erasure.region_rows(w[i]), "primary:P-C")
    assert out["E3_site_primary_X1"] == direct
    assert set(out["E3_site_primary_X1"]) >= {"linear", "mlp", "pass", "mlp_exceeds_margin"}
    st = out["E3_state_primary_X1"]
    assert st["applicable"] and st["retained_fraction"] == pytest.approx(
        out["E2_primary_after_removal_X1"]["delta_auc"] / 0.1)
    assert checks.e3_state_retention({"pass": False}, out["E2_primary_after_removal_X1"])["applicable"] is False


# --------------------------------------------------------------------------------------- T3: learner restriction --
def test_t3_x2_linear_only_and_equals_locked_call(ph):
    from ss_benchmark import arms, dgp, grid, sdr, seeds
    from xplore import x_units
    cell = grid.all_cells()[2]
    recs = x_units.unit_records(ph["D"], cell, 0, ph["root"], ph["orig"], C.X_ARMS, C.ANALYSES["X2"], "X2")
    assert [r["arm"] for r in recs] == list(C.X_ARMS)
    assert all(r["mode"] == "linear" and r["n_outcome_mlp"] == 0 and r["n_ratio_mlp"] == 0 for r in recs)
    seq = seeds.replicate_seq(cell.index, 0, ph["root"])
    d = dgp.draw(ph["D"], cell, seq)
    A, Y = dgp.simulate(ph["D"], cell, d)
    X = arms.arm_covariates("FM-S-C", ph["D"], cell, d, ph["orig"])
    e = sdr.sdr_mtp(A, Y, X, cell.W, cell.K, ph["D"].folds, seeds.child(seq, "learners"), "linear")
    assert all(json.dumps(recs[1][k]) == json.dumps(v) for k, v in e.items())
    assert C.ANALYSES == {"X1": "select", "X2": "linear"}


def test_t3_x1_select_mode(ph, x1):
    from ss_benchmark import grid
    from xplore import x_units
    feats, _, _ = x1
    recs = x_units.unit_records(ph["D"], grid.all_cells()[2], 0, ph["root"], feats, ("FM-P-C",), C.ANALYSES["X1"], "X1")
    assert recs[0]["mode"] == "select" and recs[0]["analysis"] == "X1"


# ------------------------------------------------------------------------------------------------- T4: control C0 --
def test_t4_c0_reproduces_locked_unit_and_detects_change(ph, tmp_path):
    from xplore import x_units
    work = locked_step6_shards(ph, str(tmp_path), C.C0_CELLS, C.C0_REPS, ("FM-P-C",))
    res = x_units.control_c0(ph["D"], ph["root"], ph["orig"], work, C.C0_CELLS, C.C0_REPS)
    assert res["passed"] and len(res["units"]) == 4 and all(u["fields_compared"] > 10 for u in res["units"])
    bad = {k: v.copy() for k, v in ph["orig"].items()}
    bad["P-C"][:, 0, 0, 0] += 1e-6
    res2 = x_units.control_c0(ph["D"], ph["root"], bad, work, C.C0_CELLS, C.C0_REPS)
    assert not res2["passed"]


# -------------------------------------------------------------------------------- synthetic frames (T5 - T7) --
def frames(cells=(2, 18), M=4, seed=1):
    from xplore.x_compare import STEP6_ARMS
    rng = np.random.default_rng(seed)
    truth = {(c, r): float(rng.uniform(0.05, 0.2)) for c in cells for r in range(M)}

    def rec(c, r, arm, an=None):
        est = truth[(c, r)] + rng.normal(0, 0.02)
        se = 0.01
        return dict(cell=c, rep=r, arm=arm, truth=truth[(c, r)], est=est, se=se, ci_lo=est - 1.96 * se,
                    ci_hi=est + 1.96 * se, support_failure=False, ess_min=0.5, ratio_min=0.9, ratio_max=1.1,
                    n_outcome_mlp=0, n_ratio_mlp=0, mode=C.ANALYSES.get(an, "select"), analysis=an)
    x = pd.DataFrame([rec(c, r, a, an) for an in C.ANALYSES for c in cells for r in range(M) for a in C.X_ARMS])
    s6 = pd.DataFrame([rec(c, r, a) for c in cells for r in range(M) for a in STEP6_ARMS])
    return x, s6


def test_t5_pairing_check():
    from xplore import x_compare
    cells, M = (2, 18), 4
    x, s6 = frames(cells, M)
    assert x_compare.pairing_check(x, s6, tuple(C.ANALYSES), cells, M)["passed"]
    x2 = x.copy()
    i = x2.index[0]
    x2.loc[x2.index[(x2.cell == x2.at[i, "cell"]) & (x2.rep == x2.at[i, "rep"]) & (x2.analysis == x2.at[i, "analysis"])],
           "truth"] = np.nextafter(x2.at[i, "truth"], 1.0)
    with pytest.raises(x_compare.PairingError):
        x_compare.pairing_check(x2, s6, tuple(C.ANALYSES), cells, M)
    with pytest.raises(x_compare.PairingError):
        x_compare.pairing_check(x[~((x.cell == 2) & (x.rep == 3) & (x.analysis == "X2"))], s6, tuple(C.ANALYSES),
                                cells, M)
    with pytest.raises(x_compare.PairingError):
        x_compare.pairing_check(x, s6[~((s6.cell == 18) & (s6.rep == 1) & (s6.arm == "NV"))], tuple(C.ANALYSES),
                                cells, M)


def test_t6_bootstrap_determinism_formula_identity_seeds():
    from xplore import x_compare
    x, s6 = frames((2, 18, 15), 6, seed=3)
    groups = {"g": [2, 15, 18]}
    a1, g1 = x_compare.compare(x, s6, tuple(C.ANALYSES), groups, n_boot=200)
    a2, g2 = x_compare.compare(x, s6, tuple(C.ANALYSES), groups, n_boot=200)
    pd.testing.assert_frame_equal(a1, a2)
    pd.testing.assert_frame_equal(g1, g2)
    r = a1[(a1.analysis == "X1") & (a1.arm == "FM-S-C") & (a1.comparison == "FM") & (a1.cell == 15)].iloc[0]
    A = x[(x.analysis == "X1") & (x.arm == "FM-S-C") & (x.cell == 15)].sort_values("rep")
    B = s6[(s6.arm == "FM-S") & (s6.cell == 15)].sort_values("rep")
    hand = (abs((A.est.to_numpy() - A.truth.to_numpy()).mean()) - abs((B.est.to_numpy() - B.truth.to_numpy()).mean())) \
        / A.truth.mean()
    assert r.delta == pytest.approx(hand, abs=1e-15)
    for _, gr in g1.iterrows():
        sub = a1[(a1.analysis == gr.analysis) & (a1.arm == gr.arm) & (a1.comparison == gr.comparison)]
        assert gr.mean_delta == pytest.approx(sub.delta.mean(), abs=1e-15)
        assert gr.n_cells_delta_negative == int((sub.delta < 0).sum())
    assert all(n.startswith("exploratory:") and not n.startswith("family:") for n in pd.concat([a1, g1]).seed_name)
    assert "exploratory:X1:FM-P-C:step6-FM-P:15" in set(a1.seed_name)
    s6i = s6.copy()                                             # identity: comparator equals the X arm
    for arm in C.X_ARMS:
        for comp_arm in (arm,):
            src = x[(x.analysis == "X1") & (x.arm == arm)].set_index(["cell", "rep"])
            m = s6i.arm == comp_arm
            s6i.loc[m, "est"] = [src.loc[(c, rr), "est"] for c, rr in zip(s6i[m].cell, s6i[m].rep)]
            s6i.loc[m, "ci_lo"] = [src.loc[(c, rr), "ci_lo"] for c, rr in zip(s6i[m].cell, s6i[m].rep)]
            s6i.loc[m, "ci_hi"] = [src.loc[(c, rr), "ci_hi"] for c, rr in zip(s6i[m].cell, s6i[m].rep)]
    ai, _ = x_compare.compare(x[x.analysis == "X1"], s6i, ("X1",), groups, n_boot=200)
    z = ai[ai.comparison == "minusC"]
    assert (z[["delta", "delta_lo", "delta_hi", "cov_diff", "cov_diff_lo", "cov_diff_hi"]].to_numpy() == 0).all()


def test_t7_report_wording_and_all_cells():
    from xplore import x_compare
    cells = (2, 15, 18)
    x, s6 = frames(cells, 5, seed=4)
    groups = {"P2-FM": [2], "slice": [15], "P1b-FM": [18]}
    metrics = x_compare.x_cell_metrics(x)
    cd, gd = x_compare.compare(x, s6, tuple(C.ANALYSES), groups, n_boot=100)
    site = {"linear": dict(ba=0.25, upper_one_sided_95=0.3), "mlp": dict(ba=0.6, upper_one_sided_95=0.7)}
    e3 = {k: {"E3_site_primary_X1": site, "E3_state_primary_X1": {"applicable": False},
              "step5_reference": {"E3_site_primary": {"linear": {"upper_one_sided_95": 0.47}}}} for k in ("P", "S")}
    er = {"P": [dict(fold=0, n_fit_cases=1, n_fit_rows=75, leace_rank=3, leace_identities={"a": 1e-15},
                     leace_var_retained=0.9)]}
    c0 = {"passed": True, "units": [{"cell": 2, "rep": 0}]}
    text = x_compare.report({"x_commit": "abc"}, {"pairs_checked": 30}, c0, er, e3, metrics, cd, gd, True)
    for w in x_compare.BANNED:
        assert w not in text
    for an in C.ANALYSES:
        for arm in C.X_ARMS:
            assert f"**{an} ({C.ANALYSES[an]}): {arm}**" in text
    assert sum(1 for line in text.splitlines() if line.startswith(("| 2 |", "| 15 |", "| 18 |"))) == 3 * 3 * 2
    assert "no longer exceeds the prespecified linear site-encoding boundary" in text
