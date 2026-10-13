# Related-work notes for the manuscript (Introduction and Discussion)

* **Task:** `CC_TASK_SS_exploratory_followup_v1.md` §3. Written 2026-10-13, without any step-6 result.
* **Sources of every reference:**
  * every identifier, year and venue comes from the stored API records (`records_raw.jsonl`), checked by `build_notes.py`;
  * descriptions come from the abstracts quoted in `LIT_CHECK_ERASURE.md`, or from the full texts in `FULLTEXT_CHECK.md` where marked "Full text checked";
  * record keys (Q4-a …) refer to `LIT_CHECK_ERASURE.md`.
* **Labels:**
  * **extension of prior work**: prior work shows the phenomenon, and our study extends it to a new setting.
  * **not found in the searched literature**: not found in the 166 queries in four indexes, read at abstract level plus four full texts. This is not a claim that it has never been done; never write "first".
* **Our results:**
  * The only results cited are the committed step-5 E3 values, as recorded in `EXPLORATORY_PLAN_X1_X2.md`.
  * Step-6, X1 and X2 results do not exist here. Statements about them describe what the study examines, not what it found.

## 1. Instrument adjustment and bias amplification (single time point)

**References (verified):**

* [Q4-b] *On a Class of Bias-Amplifying Variables that Endanger Effect Estimates*. arXiv (Cornell University), 2012. DOI 10.48550/arxiv.1203.3503.
  * Conditioning on instruments amplifies unmeasured-confounding bias. This extends to nonlinear models less sweepingly, and can create bias where none existed.
* [Q4-c] *Reducing Bias Amplification in the Presence of Unmeasured Confounding through Out-of-Sample Estimation Strategies for the Disease Risk Score*. Journal of Causal Inference, 2014. DOI 10.1515/jci-2014-0009; PMID 25313347.
  * Controlling for predictors of treatment (instruments and measured confounders) amplifies the bias from unmeasured confounders; DRS-based mitigation.
* *Principles of confounder selection*. European Journal of Epidemiology, 2019. DOI 10.1007/s10654-019-00494-6; PMID 30840181.
  * A practical rule: control for causes of exposure or outcome, but exclude any variable known to be an instrument.
* [Q4-d] *Causal Simulation Experiments: Lessons from Bias Amplification*. arXiv, 2020. arXiv 2003.08449.
  * Simulations in clinical settings suggest the amplification is often smaller in practice than theory suggests.
* [Q4-e] *Modeling Versus Balancing Approaches to Addressing Instrumental Variables in Weighting: A Comparison of the Outcome‐Adaptive Lasso, Stable Balancing Weighting, and Stable Confounder Selection*. Pharmacoepidemiology and Drug Safety, 2025. DOI 10.1002/pds.70173; PMID 40576288.
  * Instruments in propensity-score weighting affect bias and precision and can cause practical positivity violations.
* [Q4-f] *Bias amplification of unobserved confounding in pharmacoepidemiological studies using indication‐based sampling*. Pharmacoepidemiology and Drug Safety, 2023. DOI 10.1002/pds.5614; PMID 36919941.
  * Restricting the sample on a treatment predictor (indication) can amplify unobserved-confounding bias.
* [Q4-g] *Optimal Covariate Adjustment beyond the Average Treatment Effect: Treated-Population and Overlap-Weighted Estimands*. arXiv, 2026. arXiv 2609.11222.
  * For weighted estimands with propensity-dependent weights (e.g., overlap weights), instrument adjustment changes the estimand itself ("estimand drift").

**Not retrieved by our searches.** These appear in the reference list of Q4-a (PDF p. 10), copied verbatim. They have no stored record or identifier; retrieve and check each before citing it:

* Myers JA, Rassen JA, Gagne JJ, Huybrechts KF, Schneeweiss S, Rothman KJ, et al. Effects of adjusting for instrumental variables on Bias and precision of effect estimates. Am J Epidemiol. 2011;174:1213–22.
* Ding P, Vanderweele TJ, Robins JM. Instrumental variables as bias amplifiers with general outcome and confounding. Biometrika. 2017;104:291–302.
* Pearl J. Invited commentary: understanding Bias amplification. Am J Epidemiol. 2011;174:1223–7.
* Wooldridge JM. Should instrumental variables be used as matching variables? Res Econ. 2016;70:232–7.

**How our study relates:**

* *extension of prior work*: Our with/without-centre (C) contrasts ask whether this phenomenon appears when the instrument-like variable is a centre, in a sequential design (§2).

## 2. Longitudinal extension

**References (verified):**

* [Q4-a] *Bias amplification in the g-computation algorithm for time-varying treatments: a case study of industry payments and prescription of opioid products*. BMC Medical Research Methodology, 2022. DOI 10.1186/s12874-022-01563-3; PMID 35468735.
  * Full text checked (`FULLTEXT_CHECK.md`):
    * the setting is two time points, static regimes and parametric g-computation;
    * adjusting for a perfect time-fixed instrument raised the bias by about +0.3 percentage points on 4–6 points of baseline bias (N = 200,000);
    * the effect reversed for near-instruments tied to the unmeasured confounder (β1 ≥ 0.1).

**How our study relates:**

* *extension of prior work*: Instrument adjustment amplifying bias under time-varying treatment is already shown, for generic instruments and static regimes. Our results bear on it only as an extension.
* *not found in the searched literature*: A centre variable as the instrument-like covariate in sequential adjustment.
* *not found in the searched literature*: Instrument-like adjustment in a modified treatment policy (or an incremental/stochastic intervention).
* *not found in the searched literature*: Instrument-like adjustment with a sequential doubly robust estimator.
* *not found in the searched literature*: Instrument-like information carried implicitly by learned representations.

## 3. Site harmonization and residual site information

**References (verified):**

* [Q2-a] *Removing the effects of the site in brain imaging machine-learning - Measurement and extendable benchmark*. NeuroImage, 2022. DOI 10.1016/j.neuroimage.2022.119800; PMID 36481413.
  * ComBat removes simple site effects (enough for lasso) but leaves complex effects that can bias SVM predictions.
* [Q2-b] *Mitigating site effects in covariance for machine learning in neuroimaging data*. Human Brain Mapping, 2021. DOI 10.1002/hbm.25688; PMID 34904312.
  * Removing site effects in mean and variance may not be enough for ML, because site also lives in the covariance.
* [Q2-c] *DeepComBat: A statistically motivated, hyperparameter-robust, deep learning approach to harmonization of neuroimaging data*. Human Brain Mapping, 2024. DOI 10.1002/hbm.26708; PMID 39056477.
  * Significant multivariate batch effects remain after state-of-the-art harmonization.
* [Q2-d] *Machine Learning with Multi-Site Imaging Data: An Empirical Study on the Impact of Scanner Effects*. arXiv, 2019. arXiv 1910.04597.
  * A classifier identifies data origin with very high accuracy after pre-processing; harmonization does not remove scanner bias.
* [Q2-e] *Failure to Achieve Domain Invariance With Domain Generalization Algorithms: An Analysis in Medical Imaging*. IEEE Access, 2023. DOI 10.1109/ACCESS.2023.3268704.
  * Domain-generalization training leaves substantial domain information in medical-imaging features.
* [Q2-k] *Dataset-Specific Encoding of Image Content Underlies Cross-Dataset Failure in Brain MRI Foundation Models*. arXiv, 2026. arXiv 2610.13027.
  * LEACE/INLP removal of dataset signal from brain-MRI foundation-model features does not improve transfer (preprint).
* [Q2-x1] *Deep feature batch correction using ComBat for machine learning applications in computational pathology*. Journal of Pathology Informatics, 2024. DOI 10.1016/j.jpi.2024.100396; PMID 39398947.
  * Contrary: ComBat on pathology foundation-model embeddings brought an attention-MIL site probe to about chance.
* [Q2-x2] *Cross‐Scanner Harmonization of Neuromelanin‐Sensitive MRI for Multisite Studies*. Journal of Magnetic Resonance Imaging, 2021. DOI 10.1002/jmri.27679; PMID 33960063.
  * Contrary: after ComBat, SVM scanner classification was at chance.

**How our study relates:**

* *extension of prior work*: Site remaining decodable by nonlinear probes after linear removal is established in medical imaging. Our MLP result after LEACE (step 5, 278-case set: BA P 0.957, S 0.495, REF 0.863) is a new instance, in surgical-video foundation-model embeddings. The contrary records show the outcome is not universal.

## 4. Linear concept erasure and its limits

**References (verified):**

* *LEACE: Perfect linear concept erasure in closed form*. Neural Information Processing Systems, 2023. DOI 10.52202/075280-2884; arXiv 2306.03819.
  * Closed-form erasure that provably prevents all linear classifiers from detecting the concept (the method we use).
* *Null It Out: Guarding Protected Attributes by Iterative Nullspace Projection*. Annual Meeting of the Association for Computational Linguistics, 2020. DOI 10.18653/v1/2020.acl-main.647; arXiv 2004.07667.
  * INLP: iterative nullspace projection.
* *Linear Adversarial Concept Erasure*. International Conference on Machine Learning, 2022. arXiv 2201.12091.
  * R-LACE: linear minimax concept erasure.
* *Better Hit the Nail on the Head than Beat around the Bush: Removing Protected Attributes with a Single Projection*. Conference on Empirical Methods in Natural Language Processing, 2022. arXiv 2212.04273.
  * Mean projection (MP) as a single targeted projection.
* [Q2-f] *Adversarial Removal of Demographic Attributes from Text Data*. Conference on Empirical Methods in Natural Language Processing, 2018. DOI 10.18653/v1/D18-1002; arXiv 1808.06640.
  * A post-hoc classifier recovers attributes after adversarial removal.
* [Q2-g] *Adversarial Concept Erasure in Kernel Space*. Conference on Empirical Methods in Natural Language Processing, 2022. DOI 10.18653/v1/2022.emnlp-main.405; arXiv 2201.12191.
  * Protection against one nonlinear adversary does not transfer to others.
* [Q2-h] *Obliviator Reveals the Cost of Nonlinear Guardedness in Concept Erasure*. The Thirty-Ninth Annual Conference on Neural Information Processing Systems 2025, 2026. arXiv 2603.07529.
  * Existing erasure methods remain vulnerable to nonlinear adversaries. (OpenAlex gives year 2026 and the venue as NeurIPS 2025; check before citing.)
* [Q2-j] *Log-linear Guardedness and its Implications*. Annual Meeting of the Association for Computational Linguistics (ACL), 2023. DOI 10.18653/v1/2023.acl-long.523; arXiv 2210.10012.
  * A downstream multiclass log-linear model can recover a linearly erased concept indirectly.
* [Q1-a] *A framework for analyzing concept representations in neural models*. Conference on Computational Natural Language Learning, 2026. DOI 10.18653/v1/2026.conll-main.34; arXiv 2605.01381.
  * Full text checked: LEACE leaks on held-out data under linear probes (Table 5: 29.6 % phones, 54.4 % speakers vs best cases 7.8 / 2.7).
* [Q1-b] *Detecting a Shift Is Not Enough: Exact Minimax Limits of Linear Representation Repair*. arXiv, 2026. arXiv 2610.08069.
  * Full text checked: finite-calibration linear erasers (MP, SAL, LEACE) leave a predictable share of a device shift in new participants, and remove only first-moment differences (preprint).
* [Q1-c] *Impossibility results for fair representations*. arXiv, 2021. arXiv 2107.03483.
  * Full text checked: no fixed representation keeps demographic-parity fairness under every change of the marginal, including the uniform distribution over a subset (theory, worst case).
* [Q2-x3] *Adversarial Removal of Demographic Attributes Revisited*. Conference on Empirical Methods in Natural Language Processing, 2019. DOI 10.18653/v1/D19-1662.
  * Caution: leakage detected after removal may not generalize to new samples.

**How our study relates:**

* *extension of prior work*: Nonlinear recovery after linear erasure, and LEACE's guarantee failing on held-out data, are established. Our MLP result after LEACE is a further instance.
* *not found in the searched literature*: A linear eraser fitted on a cohort (278 cases; linear site BA 0.250 = chance for 4 centres) failing on a prespecified, window-selected subset of that same cohort (158 cases; BA 0.393–0.448). Q1-c gives a worst-case existence argument that such subsets can exist, but no record shows it for a natural selection rule.

## 5. Representation adjustment in causal inference

**References (verified):**

* *Adapting Text Embeddings for Causal Inference*. Conference on Uncertainty in Artificial Intelligence, 2019. arXiv 1905.12741.
  * Causally sufficient low-dimensional embeddings of text used for adjustment.
* *Text and Causal Inference: A Review of Using Text to Remove Confounding from Causal Estimates*. Annual Meeting of the Association for Computational Linguistics (ACL), 2020. DOI 10.18653/v1/2020.acl-main.474; arXiv 2005.00649.
  * Review of using text to remove confounding.
* *Estimating Causal Effects Under Image Confounding Bias with an Application to Poverty in Africa*. arXiv, 2022. arXiv 2206.06410.
  * Conditions for identification and estimation when images carry the confounding.
* [Q3-a] *Adjustment for Confounding using Pre-Trained Representations*. International Conference on Machine Learning, 2025. arXiv 2506.14329.
  * Conditions for valid ATE adjustment with pretrained features. Additive or sparse linear nuisance assumptions are unrealistic for latent features.
* [Q3-d] *Reading Between the Lines: Deconfounding Causal Estimates using Text Embeddings and Deep Learning*. arXiv, 2026. arXiv 2601.01511.
  * Tree-based DML retains substantial bias with embeddings; neural nuisances reduce it (synthetic, preprint).
* [Q3-b] *The Confounder Trap: Treatment-Encoding Representations in Causal Inference with Text*. arXiv, 2026. arXiv 2607.26309.
  * Representations that encode the treatment induce overlap violations (text, preprint).
* [Q3-c] *Detecting and Mitigating Treatment Leakage in Text-Based Causal Inference: Distillation and Sensitivity Analysis*. arXiv, 2025. arXiv 2601.02400.
  * INLP and other distillation remove treatment-predictive text before adjustment (preprint).
* [Q3-e] *Causal Inference with Video Features as Treatments*. arXiv, 2026. arXiv 2607.06126.
  * Learned video representations inside a sequential stochastic-intervention estimator, with video features as the treatment (preprint).

**How our study relates:**

* *extension of prior work*: Adjusting for learned representations, and the dependence on the nuisance-learner class (X2: linear vs MLP nuisances), are covered by prior work. Our sequential MTP with SDR on surgical-video foundation-model embeddings extends it.
* *not found in the searched literature*: The consequence for a causal estimate of site information left in representations after erasure or harmonization, in a single-time or sequential design. Whether our step 6, X1 or X2 show such a consequence is not yet known.

## Claims at a glance

| claim | label | basis |
|---|---|---|
| Adjusting for an instrument-like variable can amplify bias under time-varying treatment | extension of prior work | Q4-a (full text) |
| Centre as the instrument-like covariate in a sequential MTP with an SDR estimator | not found in the searched literature | §2 |
| Site remains decodable by nonlinear probes after linear removal | extension of prior work | Q2-a–e; Q2-f–j (NLP) |
| LEACE's guarantee does not extend to held-out data | extension of prior work | Q1-a (full text) |
| An eraser fitted on a cohort fails on a prespecified window-selected subset of that cohort | not found in the searched literature | §4; Q1-c is worst-case theory only |
| Nuisance-learner class matters when adjusting for learned representations | extension of prior work | Q3-a, Q3-d |
| Residual site information after erasure changes causal estimates | not found in the searched literature | §5 (our step 6 / X1 / X2 not yet known) |
