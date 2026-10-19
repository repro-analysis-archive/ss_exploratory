# X1 / X2 implementation notes

* **Written:** 2026-10-19, under `CC_TASK_SS_X1X2_prep_v1.md`.
* **No X result existed when these notes were written.**
  * No X unit has been run on real data.
  * The real step-5 representations were read only to check their layout (array names, shapes, case lengths).
  * No step-6 replicate was read.
* **Governing document:** `EXPLORATORY_PLAN_X1_X2.md` (commit `b6d1cf7`; OSF https://osf.io/5c627). The plan governs.
* **What this file records:** where the plan or the task left a point open, the choice made and why.
* **What no choice changes:** cells, replicates, seeds, outcomes or wording rules.

## Choices

**N1. Output folder and runner name.**
* The task text says `/media/user/LaCie/medvideo_gate/ss_X/` and `run_X.sh`. The plan (§7) says `/media/user/LaCie/medvideo_gate/ss_exploratory_X/` and `run_x.sh`.
* The task states that the plan governs, so the plan's names are used.

**N2. "The main repository's HEAD is the step-7 record commit."**
* The runner accepts the main repository's HEAD if it is the step-7 record commit `2880d73` or a descendant of it, provided nothing changed under `ss_benchmark/`, `data_audit/lead/out/`, `results/step5/` or `results/step6/` since `2880d73`.
* The locked snapshot is always taken from `2880d73` itself (`git archive`, read only).
* **Reason:** the investigator may commit the step-7 report into the main repository before launching X. That changes no input of X and should not block the run.

**N3. "The step-6 shards match the committed shard list."**
* What is checked: the shards X reads, which are the 14,200 primary-set shards of the 71 cells × 200 replicates. Each must exist and have the SHA-256 listed in the committed `results/step6/shard_sha256.txt.gz` (at `2880d73`). Step 6 must also be complete (`state.json`).
* **Reason:** these are exactly the shards X uses for pairing. The full 73,200-shard digest was already verified by step 7.

**N4. The step-5 files checked** against the committed `step5_manifest.json`: `reps.npz`, `reps_full_P.npz`, `reps_full_S.npz`, `reps_full_REF.npz` and `checks.json`, i.e. everything X reads from step 5.

**N5. X1 eraser fitting and application.**
* **Fitting rows** (exactly as in plan §1), for fold v:
  * the analysis-region rows `w_i − 30 … w_i + 44` of the primary cases with fold ≠ v;
  * in the fold-v PCA coordinates of the step-5 `reps_full_<key>.npz`.
* **Application:** the eraser is applied to every representation-set case's fold-v coordinates. Only the 158 primary cases enter the windowed features and the E3 checks.
* **Bounds check:** every primary case's region lies inside its steps (lowest start row 5, smallest margin to the end 32), so no row index wraps around. The code also checks this and refuses otherwise.
* **Row count:** 11,850 rows over all 158 cases, as the plan states.

**N6. E3-state for X1.**
* `checks.e2_auc` is run on the X1 features for P, S and REF, with tag `primary:<key>-C`, as `pipeline.run_checks` does for `E2_primary_after_removal`.
* `checks.e3_state_retention` is then run against the committed step-5 `E2_primary`. It returns "not applicable" for S and REF, whose E2 primary failed at step 5.
* **Reason:** this is the locked code path unchanged.

**N7. `reps_full` unpacking.**
* `pipeline._unpack_full` cannot be imported, because importing `ss_benchmark.pipeline` loads `torch` through `extract`.
* Its four lines are reproduced in `x1_erasure.unpack_full` (same array names and the same split by `lengths`). A test checks the round trip on the `build_reps` layout.

**N8. Control C0.**
* **Cells and replicates:** cells 2 and 18 (the lowest-index P2-FM and P1b-FM cells, both K = 1), replicates 0 and 1. Arm FM-P−C, original step-5 features, mode "select".
* **"Bit for bit"** means that every field of the step-6 FM-P−C record equals the X record after a JSON round trip (compared as JSON text, so NaN-safe), and that the field sets are equal.
* **If C0 fails,** the runner stops before any X unit.

**N9. Units.**
* A unit is (analysis, cell, replicate) and runs the three arms in sequence, exactly as `grid_driver._unit`. There is one shard per unit, and the run resumes per unit.
* Records carry the `grid_driver` fields plus `analysis`.
* X1 units come first, then X2; within an analysis, units run in cell and replicate order. Order does not affect results.

**N10. Bootstrap seed names (plan §3).**
* The format is `exploratory:<X1|X2>:<arm>:step6-<comparator arm>:<cell index | group>`, for example `exploratory:X1:FM-P-C:step6-FM-P:15`.
* The group names are `P1b-FM`, `P2-FM` and `slice`.
* These names are distinct from the §12.3 family streams `family:<F>`.

**N11. Non-finite estimates.**
* **For Δ and the coverage difference:** replicate pairs in which either estimate or the truth is non-finite are dropped, as in §12.3 `family_verdict`. The count is reported (`dropped_nonfinite`).
* **Per-replicate coverage** is the `cell_metrics` definition: lo ≤ truth ≤ hi, with a finite estimate and SE.
* **The X-arm cell metrics** use the locked `grid.cell_metrics` on all replicates.

**N12. Coverage-difference interval.** It uses the same bootstrap indices as the cell's Δ.

**N13. Group bootstrap.**
* One generator per (X, arm, comparator, group). For each cell in increasing index it draws a (B, M) index matrix.
* Δ is recomputed per resample and averaged over the group's cells, with the cells fixed. This is the §12.3 scheme.

**N14. Heatmaps.**
* `X_heatmaps.pdf` has one page per (X, comparator, quantity), where the quantity is Δ or the coverage difference.
* Each page shows the three arms × all 71 cells, in cell-index order, on a diverging scale centred at 0.

**N15. Records.**
* The runner commits exactly 10 files to `results_X/` in this repository, records only, with the parent verified as `--expect-commit`:
  * `X_REPORT.md`, `X_heatmaps.pdf`;
  * `x_cell_metrics.csv`, `x_comparisons_cells.csv`, `x_comparisons_groups.csv`;
  * `x_pairing_c0.json`, `x1_erasure_report.json`, `x1_e3.json`;
  * `x_run_record.json`, `x_unit_sha256.txt.gz`.
* The X replicate rows (`x_replicates.csv.gz`) stay in the output folder; their SHA-256 is in `x_run_record.json`.

**N16. Code snapshots.** The runner runs the X code from a `git archive` of this repository at `--expect-commit` (`x_code/`), and the locked code from a `git archive` of `2880d73` (`locked_snapshot/`). Both are hashed and re-verified on resume.

**N17. Workers and threads.** 18 workers pinned to CPUs 0–17, the orchestrator on CPUs 18–19, code-lock thread settings, the base Python. These are the step-6 settings.

**N18. PLACEHOLDER mode.**
* **Design, features and replicate root:** the locked `placeholder.build()` and the `grid_driver` PLACEHOLDER root.
* **Comparators:** "step-6" shards produced by the locked `grid_driver._unit` in a throwaway directory.
* **E2 reference:** the step-5 `E2_primary` reference is computed with the locked `checks.e2_auc` on the PLACEHOLDER coordinates.
* **Scope:** used only by tests and the smoke run, which refuse the real output folder.

**N19. Comparator source.** The step-6 comparators are read from the step-6 shards (`grid/work/primary`), as plan §7 says, not from `replicates.csv`.

## Compute estimate

Computed with `xplore/x_estimate.py`:
* **Method:** plan §8, the code-lock timing table (mean wall time per fit by K, W, arm and mode), × 200 replicates, over the 71 cells and the 3 arms.
* **Calibration:** the code-lock projection of step 6 (5.99 days at 20 workers = 575,054 s at 18 workers) against step 6's actual wall time of 539,632 s (2026-10-12 14:26:42 → 2026-10-18 20:20:34). The ratio is 0.938.

| part | fit-seconds | projected at 18 workers | calibrated |
|---|---:|---:|---:|
| X1 units ("select") | 666,808 | 10.29 h | **9.66 h** |
| X2 units ("linear") | 51,724 | 0.80 h | **0.75 h** |
| input verification, snapshots, C0, X1 erasure + E3, comparison and report | — | — | about 0.2–0.4 h |
| **total** | | | **about 10.6–10.8 h (≈ 11 h)** |

Measured on PLACEHOLDER inputs of the same size (2 threads): the X1 E3 checks take about 31 s per key, against the plan's 0.5–1 h; a K = 1 unit takes about 3 s per arm in "select" mode.

## Test criteria (fixed before any test was run)

**T1. X1 eraser (PLACEHOLDER).** For each key P, S, REF and each fold:
* the number of fitting rows equals 75 × the number of primary cases with fold ≠ v;
* the rank is 3 (four centres);
* the identities hold on the fitting rows: idempotence, erased cross-covariance and erased covariance with site all ≤ 1e-8;
* the windowed features have shape (5, 158, 15, 64);
* changing the coordinates of a non-primary case, or of a primary case in fold v, leaves the fold-v eraser unchanged;
* the X1 features differ from the protocol (278-case) PLACEHOLDER features;
* `unpack_full` round-trips the `build_reps` `_full` layout exactly.

**T2. X1 E3 (PLACEHOLDER, key P).**
* `x1_checks` returns linear and MLP results.
* Its E3-site numbers equal a direct call of the locked `checks.e3_site` with tag `primary:P-C`.
* E3-state is "not applicable" when the reference E2 fails, and a retained fraction when it passes.

**T3. Learner restriction.**
* X2 records have mode "linear" and zero MLP fits (`n_outcome_mlp = n_ratio_mlp = 0`) in every arm; X1 records have mode "select".
* The arms are exactly FM-P−C, FM-S−C and REF−C.
* An X2 record equals a direct call of the locked `sdr.sdr_mtp(..., mode="linear")` with the same seed.

**T4. Control C0 (PLACEHOLDER).**
* `control_c0` with the original PLACEHOLDER features reproduces the locked `grid_driver._unit` FM-P−C records for cells 2 and 18 × replicates 0 and 1 (passed = True).
* Perturbing one feature value by 1e-6 makes it fail.

**T5. Pairing.** `pairing_check` passes on consistent data and raises if:
* one truth differs by one ulp;
* an X replicate is missing;
* a step-6 comparator arm is missing.

**T6. Bootstrap.**
* `compare` is deterministic: two calls give identical frames.
* Cell Δ equals the hand formula.
* With A identical to B, every Δ, every interval bound and every coverage difference is exactly 0.
* Seed names follow N10 and never equal a `family:<F>` stream.
* The group mean Δ equals the mean of its cells' Δ, and the count of cells with Δ < 0 is correct.

**T7. Report.**
* No banned wording: SUPPORTED, CONTRADICTED, "consistent with the theory-motivated direction", "eliminated", "equivalent to chance".
* Every (analysis, arm, cell) has a row in the per-cell tables.

**T8. Runner.**
* Without `--expect-commit` it refuses with exit 3 and writes nothing.
* It refuses on a dirty tree.
* `--status` prints no estimate, bias or Δ.

**S. Smoke run (PLACEHOLDER).**
* **Setup:** a throwaway clone of this repository; cells 2, 15, 18; 3 replicates; 2 workers on CPUs 18–19; B = 200.
* **Interrupt and resume:**
  * stopped with `--stop` after at least one X1 shard exists: state "stopped", resumable;
  * relaunched with the same command: complete.
* **Results:** C0 passed, pairing passed, and a record commit of exactly the 10 record files whose parent is the launch commit.
* **Afterwards:** the outputs and the clone are deleted.
