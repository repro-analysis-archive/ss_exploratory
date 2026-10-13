# Exploratory analysis plan X1 / X2 (fixed before any step-6 result is seen)

* **Written:** 2026-10-13, while §14 step 6 was running.
* **Authority:** `CC_TASK_SS_exploratory_plan_v1.md` (investigator).
* **Blind to step 6.** No step-6 output was opened, listed or read: nothing under `/media/user/LaCie/medvideo_gate/ss_step6/` and no step-6 log.
* **Inputs read:**
  * the frozen protocol `docs/SS_PROTOCOL_DS203.md` (`4c86dc5`);
  * the locked code `ss_benchmark/` (SDR commit `af56777`);
  * the committed step-5 and §13 records `results/step5/{checks.json, section13.json, grid_conditions.json, STEP5_RECORD.md}`;
  * the code-lock timing table `results/codelock_gate/projection_PLACEHOLDER_timings.csv`.

## 0. Status: exploratory, outside the frozen protocol

**X1 and X2 are exploratory analyses outside the frozen protocol.**
* They produce **no family verdicts** and do not alter, replace or "rescue" any §12 / §13 result:
  * P1b-FM and P2-FM remain not tested (§13);
  * FM vs FM−C comparisons in the protocol grid remain descriptive only.
* They are reported in a separate, clearly labelled exploratory section.

**Motivation (committed step-5 record; values to 3 decimals):**
* After the protocol LEACE (fitted on all steps of the training-fold cases of the 278-case set), E3-site passed on the 278-case set: linear BA 0.250 for P, S and REF.
* It failed on the 158-case primary set (analysis region): linear BA P 0.416, S 0.393, REF 0.448, with 2.5 % bounds 0.352 / 0.346 / 0.387 and one-sided 95 % upper bounds 0.472 / 0.435 / 0.505 > 0.35.
* The 2-layer MLP still decoded site after LEACE on the 278-case set: BA P 0.957, S 0.495, REF 0.863.
* `grid_conditions.json`: E1 = true, E3-site = false, E3-state = true.

**Two questions:**
* **X1:** does an eraser fitted on the population and time window actually analysed remove linear site information there, and how do the FM−C arms behave with it?
* **X2:** does restricting the nuisance learners to linear ones change the FM−C arms, given that linear removal leaves nonlinearly decodable site information that an MLP nuisance could use?

## 1. Analyses

**X1: erasure fitted on the analysis population.**
* For each fold v of the fixed §2 split, a LEACE eraser is fitted with the locked `reduce.fit_leace` (unchanged) on:
  * the fold-v PCA coordinates (the protocol's 64 PCs from the 278-case PCA; **the PCA is not refitted**);
  * of the analysis-region steps (window-relative −30 … 44, §7.2; the rows E3 uses for the 158-case set);
  * of the **training-fold cases of the 158-case primary set** (fold ≠ v);
  * with the one-hot centre as the concept.
* The eraser is applied to the fold-v features of all 158 primary cases. The window-step features (steps w_i … w_i + 14) form the X1 versions of P−C, S−C and REF−C.
* The arms FM-P−C, FM-S−C and REF−C are rerun with these features. Learner mode is "select", as in step 6.
* **Why the analysis region rather than window steps 0–14 only.** It contains the window steps the estimator uses, and it is the population on which E3-site failed.

**X2: linear nuisance only.**
* The arms FM-P−C, FM-S−C and REF−C use the **original protocol (278-case) LEACE** features, from the step-5 `reps.npz` (`primary/P-C`, `primary/S-C`, `primary/REF-C`).
* The nuisance learners are restricted to the locked "linear" mode: ridge outcome regressions and L2-logistic density ratios (implementation note N12; `sdr.sdr_mtp(..., mode="linear")`).

**Not in scope:**
* the FM, NV, SITE and ORACLE arms are not rerun (their step-6 results are the comparators);
* no sensitivity set;
* no other eraser, probe or learner.

## 2. Cells

Primary set (158 cases), φ_A = 0. Cell indices are those of `ss_benchmark.grid.all_cells()`.

| group | definition | cells | indices |
|---|---|---:|---|
| P1b-FM cells (§12.2) | W = 0, P ∈ {5, 30}, all K, α, γ | 48 | 18–23, 36–41, 72–77, 90–95, 126–131, 144–149, 180–185, 198–203 |
| P2-FM cells (§12.2) | K = 1, P = 0, α > 0, all W, γ | 12 | 2–5, 8–11, 14–17 |
| main-figure slice (`PRESENTATION_DECISIONS.md`) | W = 30, α = 0.5, γ = 1, all K and P | 12 | 15, 33, 51, 69, 87, 105, 123, 141, 159, 177, 195, 213 |
| **union** | | **71** | the P2-FM and slice groups share cell 15 |

* Every one of the 71 cells is run and reported for X1 and for X2, each with the three arms.
* Fits: 71 cells × 200 replicates × 3 arms = 42,600 SDR fits per analysis.

## 3. Replicates and seeds (paired with step 6)

* **Replicates.** M = 200 per cell, with exactly the step-6 replicate seeds: `SeedSequence(20261007, spawn_key=(cell index, replicate))` (`seeds.replicate_seq`). For each unit:
  * the DGP draw (`dgp.draw`, `dgp.simulate`) and the truth (`dgp.truth`) are recomputed with the locked code; they are identical to step 6 by construction;
  * the learner stream is the same `seeds.child(seq, "learners")`.
* **Pairing.** Each X-arm replicate is paired with its step-6 counterpart (same cell, same replicate) and with the step-6 FM and NV replicates. **Pairing check:** the X truth must equal the step-6 truth exactly for every (cell, replicate); any mismatch stops the analysis.
* **Control C0 (before the run).** The X runner's code path, run with the original step-5 features and mode "select" on two cells × two replicates of FM-P−C, must reproduce the corresponding step-6 shards bit for bit. This shows that the locked estimator is used unchanged and that the seeds pair.
* **Bootstrap seeds** (§4, §5): `SeedSequence(20261008)` named children `exploratory:<X1|X2>:<arm>:<comparator>:<cell index | group>` (`seeds.child`). These are distinct from the §12.3 family streams.

## 4. E3 checks for X1's erasure (158-case set)

Run with the locked `checks` functions, unchanged, on the X1-erased features of the 158-case analysis region, for P, S and REF:
* **E3-site, linear and MLP** (`checks.e3_site`):
  * one-sided 95 % upper bound of the case-level site BA; the §5.3 boundary is 0.35;
  * the same probe and bootstrap settings and **the same tags as step 5** (`"primary:<key>-C"`, roots 20261006 / 20261008, 2,000 resamples), so the X1 and protocol E3 results are paired in their probe randomness.
* **E3-state retention** (`checks.e2_auc` on the X1 features, then `checks.e3_state_retention` against the committed step-5 `E2_primary`):
  * not applicable where E2 primary failed (S and REF in the step-5 record).
* **Reading.** The X1 eraser is fitted on training folds and evaluated on held-out folds of the same population. Linear E3-site is expected to be near chance by construction, so this is a check of the procedure, not independent evidence. The MLP result is the informative one.
* **Reporting.** E3 results for X1 are reported as they come. They do not gate X1, and X1 is reported whatever they show.

## 5. Outcomes

For every cell and arm: §11 metrics with the locked `grid.cell_metrics` (relative bias, |bias|, 95 % interval coverage, bias / MC-SD, RMSE, CI width, support-failure rate).

**Paired comparisons,** for each representation key k ∈ {P, S, REF} and each X ∈ {X1, X2}:

| comparison | meaning |
|---|---|
| X-(k−C) vs step-6 (k−C) | effect of the erasure population (X1) or of the learner restriction (X2) |
| X-(k−C) vs step-6 FM-k | site-removed (X) against site-retained |
| X-(k−C) vs step-6 NV | against no video |

* **Per cell:**
  * Δ = (|bias_A| − |bias_B|) / mean truth (A = the X arm; **negative = the X arm has smaller |bias|**);
  * the coverage difference cov_A − cov_B;
  * 95 % percentile intervals from a paired bootstrap that resamples replicates within the cell, with the same indices for both arms (B = 2,000; seeds as in §3).
* **Per group** (P1b-FM cells, P2-FM cells, main slice):
  * the mean of Δ over the group's cells, with the §12.3 bootstrap scheme (replicates resampled within cells, the same indices for both arms; cells fixed design points; B = 2,000);
  * also reported, descriptively: the number of cells with Δ < 0. No threshold is applied.
* **X1 and X2 against each other.** They are not compared directly as a contrast. Both are reported against the same step-6 comparators.

## 6. Wording rules

* Exploratory language only: "in this exploratory analysis…", "was associated with…", "Δ was … (95 % interval …)".
* **No verdicts.** No "SUPPORTED", "CONTRADICTED" or "consistent with the theory-motivated direction". No family verdict; no statement that P1b-FM / P2-FM were tested.
* **All cells reported.** All 71 cells and all arms are reported (tables and the supplementary-style heatmaps). No cell, arm, group or comparison is selected after the fact. Groups are fixed in §2.
* The §13 ceilings of the protocol grid stand unchanged. X1's E3 results are described with the §5.3 wording: "no longer exceeds the prespecified linear site-encoding boundary", never "eliminated" or "equivalent to chance".
* X1 and X2 are reported separately from the protocol results, with this plan's commit hash.

## 7. Code (new, outside the locked code, written and locked here before the run)

All new code lives in this repository (`/srv/ss_exploratory/`). It imports the locked `ss_benchmark` from a `git archive` snapshot of the main repository's step-7 record commit, checked byte-identical to the SDR commit `af56777` except the CODELOCK_CORRECTION_001 extraction adapter. It never modifies locked code.

| module | role | locked code reused unchanged |
|---|---|---|
| `xplore/x1_erasure.py` | loads the step-5 `reps_full_<key>.npz` (fold-wise PCA coordinates); fits the X1 eraser per fold on the §1 rows; writes the X1 full and windowed (`primary/<key>-C` layout) features with SHA-256 | `reduce.fit_leace`, `design.load_real_design`, `design.representation_folds` |
| `xplore/x1_checks.py` | E3-site (linear + MLP) and E3-state retention for X1 (§4) | `checks.e3_site`, `checks.e2_rows`, `checks.e2_auc`, `checks.e3_state_retention` |
| `xplore/x_units.py` | unit runner: for each (cell, replicate) draws the DGP with the step-6 seed, builds the arm covariates from the X features and runs the SDR estimator; one shard per unit; resumable; pool of workers with code-lock thread settings | `seeds.replicate_seq`, `seeds.child`, `dgp.draw`, `dgp.simulate`, `dgp.truth`, `arms.arm_covariates`, `sdr.sdr_mtp` (mode "select" for X1, "linear" for X2), `grid.all_cells` |
| `xplore/x_compare.py` | reads the step-6 shards (read-only, after step 7 is committed); pairing check; cell metrics; the paired bootstrap comparisons; the exploratory report | `grid.cell_metrics` |
| `run_x.sh` | orchestration: preconditions, snapshot, control C0, X1 erasure and checks, X1 units, X2 units, comparison; status; logs | — |
| `tests/` | PLACEHOLDER tests: C0 against the locked `grid_driver` on PLACEHOLDER features; X1 eraser identities (locked `reduce.leace_identities`); pairing check; bootstrap determinism | — |

**`run_x.sh` preconditions** (refuse otherwise):
* this repository at HEAD = `--expect-commit`, clean tree;
* the main repository's HEAD is the step-7 record commit (step 7 committed);
* its `ss_benchmark/` matches the SDR commit (adapter excepted);
* the step-5 files match the committed `step5_manifest.json` SHA-256 values;
* the step-6 shards match the committed `results/step6/shard_sha256.txt.gz`.

**Outputs** go to `/media/user/LaCie/medvideo_gate/ss_exploratory_X/`. The exploratory record (metrics, comparisons, E3 for X1, input hashes) is committed in this repository.

## 8. Compute estimate and launch

**Estimate** from the code-lock timing table (`projection_PLACEHOLDER_timings.csv`: mean wall time per SDR fit for the primary set by K, W, arm and learner mode, measured with all 20 workers busy), × 200 replicates, over the 71 cells and the three arms:

| part | fit-seconds | wall time with 18 workers |
|---|---:|---:|
| X1 units (mode "select") | 666,808 | ≈ 10.3 h |
| X2 units (mode "linear") | 51,724 | ≈ 0.8 h |
| X1 eraser and E3 checks (158-case analysis region, 3 keys; locked probes with 2,000 bootstrap resamples) | — | ≈ 0.5–1 h (estimate; about 11,850 rows per key) |
| control C0, comparisons and report | — | < 0.5 h |
| **total** | | **about 12–13 h** |

* **Launch.** By the investigator, from the terminal, after the step-7 record is committed in the main repository. It is never chained automatically to step 6 or step 7. It runs with 18 workers and the code-lock thread settings.
* **Before launch,** a later task writes and commits the code of §7 and the PLACEHOLDER tests in this repository, and records the code commit.
