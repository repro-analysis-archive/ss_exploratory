"""E3 checks on the X1 erasure (plan §4), with the locked `checks` functions unchanged.

* E3-site, linear and MLP (`checks.e3_site`) on the X1-erased features of the 158-case analysis region, with the same
  tags as step 5 ("primary:<key>-C") and the default roots (20261006 / 20261008, 2,000 resamples), exactly as
  `pipeline.run_checks` calls it for the primary set.
* E3-state retention: `checks.e2_auc` on the X1 features (tag "primary:<key>-C", as step 5's E2_primary_after_removal)
  and `checks.e3_state_retention` against the committed step-5 `E2_primary`; not applicable where E2 primary failed.
Reported as they come; they do not gate X1 (plan §4).
"""
import numpy as np

from ss_benchmark import checks

from .x1_erasure import region_rows


def x1_checks(full_x1, inp, step5_checks, n_boot=None):
    """full_x1: {key: RC_X1 (per fold, per case)}; inp: x1_erasure inputs; step5_checks: committed checks.json."""
    sites, folds, idx, w = inp["sites"], inp["folds"], inp["prim_idx"], inp["prim_w"]
    wmap = dict(zip(idx, w))
    lens = np.array([len(x) for x in next(iter(full_x1.values()))[0]])

    def region(i):
        return region_rows(wmap[i])

    kb = {} if n_boot is None else dict(n_boot=n_boot)
    rows = checks.e2_rows(idx, region, inp["switch"], lens)
    out = {}
    for key, RC in full_x1.items():
        tag = f"primary:{key}-C"
        r = {"E3_site_primary_X1": checks.e3_site(RC, idx, sites, folds, region, tag),
             "E2_primary_after_removal_X1": checks.e2_auc(rows, RC, folds, sites, tag, **kb)}
        e2_pre = step5_checks[key]["E2_primary"]
        r["E3_state_primary_X1"] = checks.e3_state_retention(e2_pre, r["E2_primary_after_removal_X1"])
        r["step5_reference"] = dict(E3_site_primary=step5_checks[key].get("E3_site_primary"),
                                    E2_primary_pass=e2_pre.get("pass"))
        r["n_rows"] = int(len(rows))
        out[key] = r
    return out
