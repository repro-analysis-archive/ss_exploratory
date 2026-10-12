# Literature check: erasure fragility and site in sequential adjustment

* **Task:** `CC_TASK_SS_literature_check_erasure_v2.md`. Run 2026-10-13.
* **Scope kept:**
  * nothing under `~/projects/medical_video_causal_gate` and nothing from the step-6 run was touched;
  * files were written only to `/srv/ss_exploratory/literature/`;
  * the Semantic Scholar key was read from `~/.config/s2/key` at run time and never printed or stored.
* **No computation.** Only literature APIs were queried.

## How the search was done

* **Sources:** PubMed (E-utilities), arXiv (export API), Semantic Scholar (Graph API) and OpenAlex (works search).
* **Queries:** 166 logged (`query_log.csv`).
  * Round 1: 6 queries per question in each of the 4 sources.
  * Round 2: 4–5 targeted queries per question in each source, plus 2 arXiv identifier look-ups.
  * arXiv got a fielded Boolean form of each query; the other sources got the plain text. Both forms are logged.
* **Records:** up to 25 per query, 2501 in total (`records_raw.jsonl`). Raw API responses are in `raw/`.
* **Screening.** I screened by title after de-duplicating titles, then read the abstracts of the shortlist.
* **Classification is from abstracts only.**
  * No full text was read, and no citation chasing was done.
  * Each quote below is verbatim from an abstract returned by an API. `build_report.py` checks this, and checks every identifier, year and venue against the stored records.
  * Abstract text is reproduced as the API returned it, including typos and LaTeX.
* **What "hits" means differs by source:**
  * PubMed: the esearch count for the query;
  * arXiv: `totalResults` for the fielded query;
  * OpenAlex: `meta.count` for its full-text search;
  * Semantic Scholar: the `total` of its relevance search. This is a very loose count (often the whole index for common words); treat it as nominal.
* **Labels:**
  * DIRECT: shows the same thing in a comparable setting.
  * PARTIAL: related, but in a different setting (e.g., NLP fairness, single time point).
  * NONE.
  * CONTRARY marks records that bear on the question but point the other way; they are reported because leaving them out would overstate the evidence.
* **Our setting**, the reference for every difference sentence: frozen foundation-model embeddings of surgical video from 4 centres, LEACE site erasure, a window-selected sub-population (158 of 278 cases) and a sequential modified treatment policy.

## Verdicts

| question | verdict | DIRECT | PARTIAL | CONTRARY |
|---|---|---|---|---|
| Q1 | PARTIAL | 0 | 3 | 0 |
| Q2 | DIRECT (with contrary evidence) | 5 | 6 | 3 |
| Q3 | PARTIAL | 0 | 6 | 0 |
| Q4 | DIRECT for generic instruments; NONE for site/centre or MTPs | 1 | 6 | 0 |

## Q1. Does a linear concept eraser (LEACE, INLP, R-LACE, mean projection or similar) fitted on one population fail to remove the concept in a sub-population or under distribution shift?

**Verdict: PARTIAL.** No retrieved record shows a linear eraser fitted on one population failing to remove the concept in a selected sub-population or time window of that population. The closest records show weaker or different things: LEACE struggling to generalise to unseen data (text, speech); an exact minimax residual of a device shift after MP/SAL/LEACE in new participants (EEG); and an impossibility result for fair representations under marginal shift.

### Q1-a [PARTIAL] A framework for analyzing concept representations in neural models

* **IDs:** DOI 10.18653/v1/2026.conll-main.34; arXiv 2605.01381
* **Year / venue:** 2026, Conference on Computational Natural Language Learning
* **Quote:**
  > "the state-of-theart concept erasure method, LEACE, performs well on both testing axes, but still struggles to generalize to unseen data"
* **Differs from our setting:** Text and speech representations, with failure on unseen data rather than on a selected sub-population or time window of the fitting population; no causal estimation.
* **Retrieved by:** Q1.1/arxiv, Q1.1/openalex, Q1.1/s2

### Q1-b [PARTIAL] Detecting a Shift Is Not Enough: Exact Minimax Limits of Linear Representation Repair

* **IDs:** arXiv 2610.08069
* **Year / venue:** 2026, arXiv
* **Quote:**
  > "Standard linear concept erasers (MP, SAL, LEACE) remove the same calibration difference, so the formula gives, before fitting, exactly how much shift they leave on fresh data and how much calibration a target requires."
  >
  > "On paired clinical and wearable sleep EEG, where differences between participants act as calibration noise, the formula predicts the device shift left in new participants"
* **Differs from our setting:** Finite-sample residual of a device mean shift in new participants after fitting on paired calibration recordings (EEG), not loss of erasure in a selected sub-population; preprint; no causal estimation.
* **Retrieved by:** Q1.1/arxiv

### Q1-c [PARTIAL] Impossibility results for fair representations

* **IDs:** arXiv 2107.03483
* **Year / venue:** 2021, arXiv
* **Quote:**
  > "even the basic goal of achieving label-independent Demographic Parity fairness fails once the marginal data distribution shifts."
* **Differs from our setting:** A theoretical result for any fixed representation and fairness of downstream classifiers under marginal shift, not linear erasure or concept decodability in a sub-population; no causal estimation.
* **Retrieved by:** Q1.102/arxiv

**Screened, not classified (Q1):**

* *Rethinking Fair Representation Learning for Performance-Sensitive Tasks* (2024; arXiv 2410.04120): fair representation learning under distribution shift across medical modalities; the abstract reports no residual attribute decodability.
* *Graph Fairness Learning under Distribution Shifts* (2024; DOI 10.1145/3589334.3645508): in-processing fairness for graph neural networks, not post-hoc erasure.
* *The Medium Is Not the Message: Deconfounding Document Embeddings via Linear Concept Erasure* (2025; DOI 10.18653/v1/2025.emnlp-main.1634): linear erasure of source/language from document embeddings for similarity tasks; no residual-decodability or causal claim.

## Q2. In medical imaging or site/scanner harmonisation, does site remain decodable after linear removal or harmonisation, especially by nonlinear probes?

**Verdict: DIRECT (with contrary evidence).** In brain MRI, several records show that site or scanner remains detectable by machine-learning probes after ComBat-type harmonisation (mean/variance removal leaves covariance and interaction effects that an SVM or other ML can use), and that domain-generalisation training leaves domain information in the features. In NLP, linear and adversarial erasure is repeatedly shown to leave the concept recoverable by nonlinear probes. **Contrary:** ComBat on pathology foundation-model patch embeddings brought a nonlinear (attention-MIL) site probe to about chance for most extractors, and ComBat on a regional MRI measure brought an SVM to chance. No record applies LEACE to site in surgical-video embeddings; the one LEACE/INLP medical-imaging record (brain-MRI foundation models) reports transfer, not residual decodability.

### Q2-a [DIRECT] Removing the effects of the site in brain imaging machine-learning - Measurement and extendable benchmark

* **IDs:** DOI 10.1016/j.neuroimage.2022.119800; PMID 36481413
* **Year / venue:** 2022, NeuroImage
* **Quote:**
  > "current Methods Aiming to Remove the EoS (MAREoS, e.g., ComBat) cannot remove complex EoS (e.g., including interactions between regions)"
  >
  > "ComBat removes all simple EoS as needed for predictions based on simple lasso algorithms, but it leaves residual complex EoS that may bias the predictions based on standard support vector machine algorithms."
* **Differs from our setting:** Tabular brain-MRI features and ComBat rather than LEACE on video embeddings; the consequence is studied for prediction accuracy, not causal estimation, and in the whole sample, not a selected sub-population.
* **Retrieved by:** Q2.100/s2

### Q2-b [DIRECT] Mitigating site effects in covariance for machine learning in neuroimaging data

* **IDs:** DOI 10.1002/hbm.25688; PMID 34904312
* **Year / venue:** 2021, Human Brain Mapping
* **Quote:**
  > "we demonstrate that methods for removing site effects in mean and variance may not be sufficient for ML. This stems from the fact that such methods fail to address how correlations between measurements can vary across sites."
* **Differs from our setting:** Cortical-thickness features with mean/variance (ComBat-type) removal, where site lives in the covariance; the abstract does not name the probe classes; no causal estimation.
* **Retrieved by:** Q2.102/s2

### Q2-c [DIRECT] DeepComBat: A statistically motivated, hyperparameter-robust, deep learning approach to harmonization of neuroimaging data.

* **IDs:** DOI 10.1002/hbm.26708; PMID 39056477
* **Year / venue:** 2024, Human Brain Mapping
* **Quote:**
  > "significant multivariate batch effects remain in the data following harmonization by current state-of-the-art statistical and deep learning methods"
* **Differs from our setting:** Brain-MRI cortical thickness harmonised with statistical and deep methods, with residual batch effects assessed by a battery of machine-learning methods; no LEACE, no sub-population and no causal estimation.
* **Retrieved by:** Q2.1/pubmed, Q2.1/s2, Q2.102/s2, Q2.2/openalex, Q3.4/openalex, Q3.4/s2

### Q2-d [DIRECT] Machine Learning with Multi-Site Imaging Data: An Empirical Study on the Impact of Scanner Effects

* **IDs:** arXiv 1910.04597
* **Year / venue:** 2019, arXiv
* **Quote:**
  > "Our results demonstrate that even after careful pre-processing with state-of-the-art neuroimaging pipelines a classifier can easily distinguish between the origin of the data with very high accuracy."
  >
  > "current approaches to harmonize data are unable to remove scanner-specific bias leading to overly optimistic performance estimates and poor generalization"
* **Differs from our setting:** Two brain-MRI studies (2 sources) after pre-processing and harmonisation, not post-hoc linear erasure of embeddings; the consequence studied is sex classification, not causal estimation.
* **Retrieved by:** Q2.1/arxiv, Q2.1/openalex, Q2.1/s2, Q2.2/arxiv

### Q2-e [DIRECT] Failure to Achieve Domain Invariance With Domain Generalization Algorithms: An Analysis in Medical Imaging

* **IDs:** DOI 10.1109/ACCESS.2023.3268704
* **Year / venue:** 2023, IEEE Access
* **Quote:**
  > "we show that all tested algorithms retain significant amounts of domain-specific information in their feature representations despite explicit training to remove it."
* **Differs from our setting:** Domain-generalisation training (invariance learned end to end) on medical image classification, not post-hoc linear erasure of frozen embeddings; no causal estimation.
* **Retrieved by:** Q2.5/openalex, Q2.5/s2

### Q2-f [PARTIAL] Adversarial Removal of Demographic Attributes from Text Data

* **IDs:** DOI 10.18653/v1/D18-1002; arXiv 1808.06640
* **Year / venue:** 2018, Conference on Empirical Methods in Natural Language Processing
* **Quote:**
  > "while the adversarial component achieves chance-level development-set accuracy during training, a post-hoc classifier, trained on the encoded sentences from the first part, still manages to reach substantially higher classification accuracies on the same data."
* **Differs from our setting:** Text, demographic attributes and adversarial (not linear post-hoc) removal; no imaging, no causal estimation.
* **Retrieved by:** Q1.101/openalex, Q1.4/arxiv, Q1.4/openalex, Q1.4/s2

### Q2-g [PARTIAL] Kernelized Concept Erasure (arXiv) / Adversarial Concept Erasure in Kernel Space (EMNLP)

* **IDs:** DOI 10.18653/v1/2022.emnlp-main.405; arXiv 2201.12191
* **Year / venue:** 2022, Conference on Empirical Methods in Natural Language Processing
* **Quote:**
  > "We demonstrate that it is possible to prevent specific non-linear adversaries from predicting the concept. However, the protection does not transfer to different nonlinear adversaries."
* **Differs from our setting:** Text (binary gender); shows that erasure guards only against the probe class it targets, here kernel adversaries; no imaging, no causal estimation.
* **Retrieved by:** Q1.3/arxiv, Q1.3/openalex, Q1.3/s2

### Q2-h [PARTIAL] Obliviator Reveals the Cost of Nonlinear Guardedness in Concept Erasure

* **IDs:** arXiv 2603.07529
* **Year / venue:** 2026, The Thirty-Ninth Annual Conference on Neural Information Processing Systems 2025
* **Quote:**
  > "While the goal of concept erasure is protection against all adversaries, existing methods remain vulnerable to nonlinear ones."
* **Differs from our setting:** General concept-erasure benchmark (social/demographic attributes), not site in medical video; no causal estimation.
* **Retrieved by:** Q1.0/openalex, Q1.1/openalex, Q1.103/arxiv, Q1.3/arxiv

### Q2-i [PARTIAL] TaCo: Targeted Concept Erasure Prevents Non-Linear Classifiers From Detecting Protected Attributes

* **IDs:** arXiv 2312.06499
* **Year / venue:** 2023, arXiv
* **Quote:**
  > "these methods typically rely on linear classifiers, which leave models vulnerable to non-linear adversaries capable of recovering sensitive information."
* **Differs from our setting:** NLP fairness (gender, ethnicity) in final-layer representations; no imaging, no causal estimation.
* **Retrieved by:** Q1.100/arxiv

### Q2-j [PARTIAL] Log-linear Guardedness and its Implications (also indexed as "Linear Guardedness and its Implications")

* **IDs:** DOI 10.18653/v1/2023.acl-long.523; arXiv 2210.10012
* **Year / venue:** 2023, Annual Meeting of the Association for Computational Linguistics (ACL)
* **Quote:**
  > "we constructively demonstrate that a multiclass log-linear model can be constructed that indirectly recovers the concept in some cases"
* **Differs from our setting:** A theoretical NLP result: a downstream multiclass model can recover an erased concept indirectly; no imaging, no causal estimation.
* **Retrieved by:** Q1.1/openalex, Q1.103/arxiv, Q1.103/openalex, Q1.103/s2

### Q2-k [PARTIAL] Dataset-Specific Encoding of Image Content Underlies Cross-Dataset Failure in Brain MRI Foundation Models

* **IDs:** arXiv 2610.13027
* **Year / venue:** 2026, arXiv
* **Quote:**
  > "Frozen features of brain MRI foundation models lose accuracy on new datasets, a failure usually blamed on the features encoding where each scan came from. We show that the failure lies elsewhere."
  >
  > "removing the dataset signal with INLP, LEACE, CORAL or adversarial training never improves sequence transfer"
* **Differs from our setting:** Closest setting found (LEACE/INLP on medical-imaging foundation-model features, dataset as the concept), but the abstract reports transfer of a content label to unseen datasets, not residual dataset decodability; brain MRI, not video; preprint; no causal estimation.
* **Retrieved by:** Q1.1/arxiv

### Q2-x1 [CONTRARY] Deep feature batch correction using ComBat for machine learning applications in computational pathology.

* **IDs:** DOI 10.1016/j.jpi.2024.100396; PMID 39398947
* **Year / venue:** 2024, Journal of Pathology Informatics
* **Quote:**
  > "Attention-based multiple instance learning models were trained to predict tissue-source site (TSS)"
  >
  > "ComBat harmonization significantly reduced the AUROC for TSS prediction, with mean AUROCs dropping to approximately 0.5 for most models, indicating successful mitigation of batch effects"
* **Differs from our setting:** Pathology foundation-model patch embeddings with ComBat and a nonlinear (attention-MIL) site probe that falls to about chance for most extractors: the closest representation setting found, with the opposite outcome; slides, not video; no causal estimation.
* **Retrieved by:** Q2.101/pubmed, Q2.101/s2

### Q2-x2 [CONTRARY] Cross‐Scanner Harmonization of Neuromelanin‐Sensitive MRI for Multisite Studies

* **IDs:** DOI 10.1002/jmri.27679; PMID 33960063
* **Year / venue:** 2021, Journal of Magnetic Resonance Imaging
* **Quote:**
  > "In the harmonized CNR, the accuracy of the SVM was at chance level (accuracy = 29.5%; P = 0.8542)."
* **Differs from our setting:** A low-dimensional regional MRI measure with ComBat, where an SVM no longer detects scanner; no embeddings, no causal estimation.
* **Retrieved by:** Q2.0/openalex, Q2.101/openalex

### Q2-x3 [CONTRARY] Adversarial Removal of Demographic Attributes Revisited

* **IDs:** DOI 10.18653/v1/D19-1662
* **Year / venue:** 2019, Conference on Empirical Methods in Natural Language Processing
* **Quote:**
  > "the diagnostic classifier generalizes poorly to both new in-domain samples and new domains, indicating that it relies on correlations specific to their particular data sample."
* **Differs from our setting:** Text; a methodological caution that residual-decodability findings must hold on new samples, relevant to how probe results after erasure are evaluated.
* **Retrieved by:** Q1.4/s2

## Q3. Has the consequence of such residual site information for causal effect estimation (confounding adjustment with learned representations) been studied?

**Verdict: PARTIAL.** No retrieved record studies how site information left after erasure or harmonisation changes a causal effect estimate. Related work covers: conditions for valid ATE adjustment with pretrained representations (including that linear/sparse nuisance models are unrealistic for latent features); representations that encode the treatment and break overlap (text); INLP used to remove treatment-predictive text before adjustment; tree-based DML retaining bias with embeddings; learned video representations in a sequential stochastic-intervention estimator (video features as the treatment); and false associations from uncorrected scanner effects (associational, not causal).

### Q3-a [PARTIAL] Adjustment for Confounding using Pre-Trained Representations

* **IDs:** arXiv 2506.14329
* **Year / venue:** 2025, Proceedings of the 42nd International Conference on Machine Learning, PMLR 267:53557-53580, 2025
* **Quote:**
  > "We formalize conditions under which these latent features enable valid adjustment and statistical inference in ATE estimation, demonstrating results along the example of double machine learning."
  >
  > "Common structural assumptions for obtaining fast convergence rates with additive or sparse linear models are shown to be unrealistic for latent features."
* **Differs from our setting:** Single-time ATE with double machine learning on pretrained features; residual site information after erasure is not studied (the linear-model point bears on X2's linear nuisance learners).
* **Retrieved by:** Q3.0/openalex, Q3.0/s2, Q3.1/openalex, Q3.102/arxiv, Q3.102/openalex

### Q3-b [PARTIAL] The Confounder Trap: Treatment-Encoding Representations in Causal Inference with Text

* **IDs:** arXiv 2607.26309
* **Year / venue:** 2026, arXiv
* **Quote:**
  > "richer representations can make treated and control documents separable, inducing overlap violations even when the underlying causal problem satisfies overlap."
* **Differs from our setting:** Text, with the treatment itself (not a site variable) encoded in the representation; single-time; remedy by masking before representation learning, not post-hoc erasure.
* **Retrieved by:** Q3.1/arxiv, Q3.1/openalex, Q3.1/s2, Q3.101/openalex, Q3.102/openalex, Q3.2/s2, Q3.3/openalex, Q3.5/s2

### Q3-c [PARTIAL] Detecting and Mitigating Treatment Leakage in Text-Based Causal Inference: Distillation and Sensitivity Analysis

* **IDs:** arXiv 2601.02400
* **Year / venue:** 2025, arXiv
* **Quote:**
  > "Treatment leakage occurs when text intended to capture confounding information also contains signals predictive of treatment status, thereby inducing post-treatment bias in causal estimates."
  >
  > "we propose four text distillation methods -- similarity-based passage removal, distant supervision classification, salient feature removal, and iterative nullspace projection -- designed to eliminate treatment-predictive content while preserving confounder information."
* **Differs from our setting:** Erasure (including INLP) inside a causal pipeline, but of treatment-predictive text, not site; single-time; the abstract does not characterise what remains after erasure.
* **Retrieved by:** Q1.2/arxiv, Q1.2/s2, Q3.1/arxiv, Q3.1/s2

### Q3-d [PARTIAL] Reading Between the Lines: Deconfounding Causal Estimates using Text Embeddings and Deep Learning

* **IDs:** arXiv 2601.01511
* **Year / venue:** 2026, arXiv
* **Quote:**
  > "standard tree-based DML estimators retain substantial bias (+24%) due to their inability to model the continuous topology of embedding manifolds."
* **Differs from our setting:** The nuisance-learner class changes the bias of adjustment for embeddings (synthetic text, single-time); no site, no erasure.
* **Retrieved by:** Q3.3/arxiv

### Q3-e [PARTIAL] Causal Inference with Video Features as Treatments

* **IDs:** arXiv 2607.06126
* **Year / venue:** 2026, arXiv
* **Quote:**
  > "we first reproduce each video using a deep generative model and leverage the model's internal representations as learned, low-dimensional summaries of video content for causal estimation. We then establish that the average potential-outcome trajectory under dynamic stochastic interventions is nonparametrically identified."
* **Differs from our setting:** Learned video representations inside a sequential stochastic-intervention estimator, but the video features are the treatment and site/erasure are not studied; entertainment/advertising video, not surgery.
* **Retrieved by:** Q3.5/arxiv, Q3.5/openalex, Q3.5/s2

### Q3-f [PARTIAL] Mitigating inter-scanner heterogeneity in brain MRI data: Assessing its impact on association analyses and the effectiveness of ComBat harmonization in multi-site neuroimaging studies

* **IDs:** DOI 10.1016/j.neuroimage.2025.121642; PMID 41380987
* **Year / venue:** 2025, NeuroImage
* **Quote:**
  > "ComBat harmonization effectively corrected the heterogeneity for most BIMs, though it was less successful for certain BIMs, particularly those related to FC."
  >
  > "when using uncorrected data, mega-analysis yielded an excessive number of significant, but unreliable, associations"
* **Differs from our setting:** Associational (not causal) analyses of tabular brain metrics; the downstream consequence is shown for uncorrected data, not for site left after harmonisation.
* **Retrieved by:** Q2.0/s2, Q2.101/s2, Q2.2/s2

**Screened, not classified (Q3):**

* *When no answer is better than a wrong answer: A causal perspective on batch effects* (2025; DOI 10.1162/imag_a_00458): treats batch-effect detection as a causal question; no downstream effect estimation with harmonised data.
* *Harmonization with Flow-based Causal Inference* (2021; arXiv 2106.06845): a counterfactual harmonisation method; no downstream causal effect estimation.
* *Quantifying Confounding Bias in Neuroimaging Datasets with Causal Inference* (2019; arXiv 1907.04102): dataset decodable from pooled MRI before any removal; no effect estimation.
* *Deconfounding Scores: Feature Representations for Causal Effect Estimation with Weak Overlap* (2021; arXiv 2104.05762): representations that improve overlap without bias; generic, no site or erasure.

## Q4. Has a site/centre variable behaving like an instrument been studied for bias amplification in longitudinal / sequential (time-varying treatment) adjustment, beyond the single-time-point case?

**Verdict: DIRECT for generic instruments; NONE for site/centre or MTPs.** One record (2022 simulation and case study) shows that adjusting for an instrument of a time-varying treatment in g-computation amplifies unmeasured-confounding bias, and that near-instruments can reduce bias when they are associated with the unmeasured confounders. All other amplification records are single time point. No retrieved record treats a site/centre variable as the instrument-like covariate in sequential adjustment, and none concerns modified treatment policies, incremental or stochastic interventions, or instrument-like information carried by learned representations.

### Q4-a [DIRECT] Bias amplification in the g-computation algorithm for time-varying treatments: a case study of industry payments and prescription of opioid products.

* **IDs:** DOI 10.1186/s12874-022-01563-3; PMID 35468735
* **Year / venue:** 2022, BMC Medical Research Methodology
* **Quote:**
  > "Conditioning on instrumental variables (IVs) is known to introduce greater bias when there is unmeasured confounding in the point-treatment settings"
  >
  > "In our simulation study, adjusting for a perfect IV of time-varying treatments in the g-computation algorithm increased bias due to unmeasured confounding, particularly when the IV had a strong relationship with the treatment."
  >
  > "this bias amplifying feature was not observed (i.e., bias due to unmeasured confounders decreased) by adjusting for near-IV when it had a stronger association with the unmeasured confounders"
* **Differs from our setting:** Generic (near-)instruments simulated for g-computation of time-varying treatment effects (multivariate-normal setting, physician-payment case study); not a site/centre variable, not a modified treatment policy or stochastic intervention, and not learned representations.
* **Retrieved by:** Q4.0/openalex, Q4.0/pubmed, Q4.0/s2, Q4.100/s2, Q4.101/openalex, Q4.101/pubmed, Q4.101/s2, Q4.3/s2, Q4.4/s2

### Q4-b [PARTIAL] On a Class of Bias-Amplifying Variables that Endanger Effect Estimates

* **IDs:** DOI 10.48550/arxiv.1203.3503
* **Year / venue:** 2012, arXiv (Cornell University)
* **Quote:**
  > "the bias-amplifying potential of instrumental variables extends over to non-linear models, though not as sweepingly as in linear models"
  >
  > "in non-linear models, conditioning on instrumental variables may introduce new bias where none existed before"
* **Differs from our setting:** Single time point, generic instruments; no sequential adjustment, no site, no representations.
* **Retrieved by:** Q4.102/openalex, Q4.2/openalex

### Q4-c [PARTIAL] Reducing Bias Amplification in the Presence of Unmeasured Confounding through Out-of-Sample Estimation Strategies for the Disease Risk Score

* **IDs:** DOI 10.1515/jci-2014-0009; PMID 25313347
* **Year / venue:** 2014, Journal of Causal Inference
* **Quote:**
  > "Both theory and simulations have shown that in the presence of unmeasured confounding, controlling for variables that affect treatment (both instrumental variables and measured confounders) amplifies the bias caused by unmeasured confounders."
* **Differs from our setting:** Single time point, disease-risk-score adjustment; no sequential policy, no site.
* **Retrieved by:** Q4.2/openalex

### Q4-d [PARTIAL] Causal Simulation Experiments: Lessons from Bias Amplification

* **IDs:** arXiv 2003.08449
* **Year / venue:** 2020, arXiv
* **Quote:**
  > "existing simulations of bias amplification in clinical settings have suggested bias amplification may not be as important in many practical cases as suggested in the theoretical literature"
* **Differs from our setting:** Single time point with a binary treatment; qualifies the practical size of amplification rather than extending it to sequential adjustment.
* **Retrieved by:** Q4.0/arxiv

### Q4-e [PARTIAL] Modeling Versus Balancing Approaches to Addressing Instrumental Variables in Weighting: A Comparison of the Outcome‐Adaptive Lasso, Stable Balancing Weighting, and Stable Confounder Selection

* **IDs:** DOI 10.1002/pds.70173; PMID 40576288
* **Year / venue:** 2025, Pharmacoepidemiology and Drug Safety
* **Quote:**
  > "Recent work shows that including instrumental variables (IVs), associated with only treatment but not with the outcome, can impact both the bias and precision of the PS-weighted estimators."
  >
  > "IVs or near-IVs may lead to practical violations of positivity assumptions"
* **Differs from our setting:** Single-time propensity-score weighting; instruments matter through positivity and precision; no sequential policy, no site.
* **Retrieved by:** Q4.104/openalex

### Q4-f [PARTIAL] Bias amplification of unobserved confounding in pharmacoepidemiological studies using indication‐based sampling

* **IDs:** DOI 10.1002/pds.5614; PMID 36919941
* **Year / venue:** 2023, Pharmacoepidemiology and Drug Safety
* **Quote:**
  > "indication-based sampling in the presence of unobserved confounding can give rise to bias amplification, a self-inflicted phenomenon where one inflates pre-existing bias through inappropriate covariate control."
* **Differs from our setting:** Single time point; amplification through restricting the sample on a treatment predictor, which is a selection mechanism but not a site variable or a sequential policy.
* **Retrieved by:** Q4.0/openalex, Q4.101/openalex

### Q4-g [PARTIAL] Optimal Covariate Adjustment beyond the Average Treatment Effect: Treated-Population and Overlap-Weighted Estimands

* **IDs:** arXiv 2609.11222
* **Year / venue:** 2026, arXiv
* **Quote:**
  > "an estimand-drift phenomenon under instrument adjustment"
* **Differs from our setting:** Single time point; weighted estimands and efficiency, not amplification of unmeasured-confounding bias in sequential adjustment.
* **Retrieved by:** Q4.id:2609.11222/arxiv

**Screened, not classified (Q4):**

* *Stochastic interventions, sensitivity analysis, and optimal transport* (2024; arXiv 2411.14285): retrieved by identifier; bounds for stochastic interventions under unmeasured confounding; the abstract has no instrument or bias-amplification content.
* *NBER TECHNICAL WORKING PAPER SERIES DO INSTRUMENTAL VARIABLES BELONG IN PROPENSITY SCORES?* (2009; none returned): Semantic Scholar returned no abstract, so no quote can be given; not classified.
* *Instrumental variable analysis to estimate treatment effects: a simulation study showing potential benefits of conditioning on hospital* (2022; DOI 10.1186/s12874-022-01598-6): hospital as an adjustment covariate in an instrumental-variable analysis; not bias amplification.
* *Using high-dimensional propensity scores to automate confounding control in a distributed medical product safety surveillance system.* (2012; PMID 22262592): mentions Z-bias only as a consideration for automated covariate selection.

## What remains novel in our results

Below, "not found" means not found in the 166 queries and abstracts above. It does not mean the work has never been done.

The step-6 results are not known; none was read. Every point about consequences for estimation is therefore an open question here, not a finding.

**1. Erasure that holds in the fitting population but not in a selected sub-population.**

* What we found (committed step-5 record, as quoted in `EXPLORATORY_PLAN_X1_X2.md`):
  * the protocol LEACE was fitted on the 278-case set, and linear site balanced accuracy there was 0.250, which is chance for 4 centres;
  * on the 158-case window-selected analysis region it was 0.393–0.448, and E3-site failed.
* Literature: no retrieved record shows this. The closest records concern unseen data or new participants (Q1-a, Q1-b) or marginal shift (Q1-c), not selection of a sub-population by window.
* **This appears novel as a documented failure mode, and as a caution for any eraser fitted before cohort or window selection.**

**2. Site still decodable by an MLP after LEACE.**

* What we found: on the 278-case set, MLP balanced accuracy was P 0.957, S 0.495, REF 0.863.
* Literature: **the phenomenon is not novel.**
  * Nonlinear recovery after linear or adversarial erasure is established in NLP (Q2-f to Q2-j).
  * Site left after ComBat-type harmonisation and detectable by ML is established in brain MRI (Q2-a to Q2-d).
* What is new is the instance: surgical-video foundation-model embeddings with LEACE.
  * It also contrasts with the pathology-embedding ComBat result (Q2-x1), so residual site after removal is not universal.
  * Because of Q2-x3, a residual-decodability claim should rest on held-out probe evaluation.

**3. What residual site information does to a causal estimate.**

* Not found for any design, single-time or sequential.
* Q3-a and Q3-d support the premise of X2: the nuisance-learner class matters when adjusting for learned representations. But neither paper involves site or erasure.
* If step 6, X1 or X2 show an effect of residual site on FM−C bias or coverage, that would be new. Whether they do is unknown.

**4. Site as an instrument-like covariate in a sequential MTP.**

* Bias amplification from adjusting for instruments of a time-varying treatment is already shown for g-computation with generic instruments (Q4-a). Any claim must be framed as an extension of it, not as the first longitudinal demonstration.
* Not found:
  * a site/centre variable as the instrument-like covariate;
  * modified treatment policies or incremental/stochastic interventions;
  * instrument-like information entering through learned representations.

**Limits of this check.**

* Abstracts only; four indexes; English queries; no citation chasing.
* Several of the closest records are recent arXiv preprints that have not been peer-reviewed (Q1-b, Q2-k, Q3-b, Q3-c, Q3-d, Q3-e).

## Query log

Copied from `query_log.csv` (one row per query and source; the time column is omitted).

| query_id | source | query | hits reported | records saved |
|---|---|---|---:|---:|
| Q1.0 | pubmed | concept erasure distribution shift | 0 | 0 |
| Q1.0 | arxiv | all:"concept erasure" AND all:shift | 7 | 7 |
| Q1.0 | s2 | concept erasure distribution shift | 7874 | 25 |
| Q1.0 | openalex | concept erasure distribution shift | 28537 | 25 |
| Q1.1 | pubmed | LEACE concept erasure | 0 | 0 |
| Q1.1 | arxiv | all:LEACE | 15 | 15 |
| Q1.1 | s2 | LEACE concept erasure | 2266 | 25 |
| Q1.1 | openalex | LEACE concept erasure | 279 | 25 |
| Q1.2 | pubmed | iterative nullspace projection protected attribute removal | 0 | 0 |
| Q1.2 | arxiv | all:"nullspace projection" | 20 | 20 |
| Q1.2 | s2 | iterative nullspace projection protected attribute removal | 30 | 25 |
| Q1.2 | openalex | iterative nullspace projection protected attribute removal | 317 | 25 |
| Q1.3 | pubmed | linear concept erasure nonlinear recovery | 0 | 0 |
| Q1.3 | arxiv | all:"concept erasure" AND all:nonlinear | 5 | 5 |
| Q1.3 | s2 | linear concept erasure nonlinear recovery | 221 | 25 |
| Q1.3 | openalex | linear concept erasure nonlinear recovery | 1461 | 25 |
| Q1.4 | pubmed | adversarial removal demographic attributes recoverable | 0 | 0 |
| Q1.4 | arxiv | all:"adversarial removal" AND all:attributes | 1 | 1 |
| Q1.4 | s2 | adversarial removal demographic attributes recoverable | 15 | 15 |
| Q1.4 | openalex | adversarial removal demographic attributes recoverable | 1974 | 25 |
| Q1.5 | pubmed | concept removal out-of-distribution subgroup | 0 | 0 |
| Q1.5 | arxiv | all:"concept removal" AND all:distribution | 7 | 7 |
| Q1.5 | s2 | concept removal out-of-distribution subgroup | 438 | 25 |
| Q1.5 | openalex | concept removal out-of-distribution subgroup | 59862 | 25 |
| Q2.0 | pubmed | ComBat harmonization site classification after harmonization | 6 | 6 |
| Q2.0 | arxiv | all:ComBat AND all:harmonization AND all:site | 16 | 16 |
| Q2.0 | s2 | ComBat harmonization site classification after harmonization | 1989 | 25 |
| Q2.0 | openalex | ComBat harmonization site classification after harmonization | 18386 | 25 |
| Q2.1 | pubmed | scanner effects remain after harmonization machine learning | 3 | 3 |
| Q2.1 | arxiv | all:scanner AND all:harmonization AND all:"machine learning" | 30 | 25 |
| Q2.1 | s2 | scanner effects remain after harmonization machine learning | 841 | 25 |
| Q2.1 | openalex | scanner effects remain after harmonization machine learning | 6016 | 25 |
| Q2.2 | pubmed | site information predictable after harmonization MRI | 6 | 6 |
| Q2.2 | arxiv | all:harmonization AND all:site AND all:predict | 79 | 25 |
| Q2.2 | s2 | site information predictable after harmonization MRI | 1795 | 25 |
| Q2.2 | openalex | site information predictable after harmonization MRI | 1437 | 25 |
| Q2.3 | pubmed | site-invariant features adversarial MRI multi-site | 1 | 1 |
| Q2.3 | arxiv | all:"site-invariant" | 12 | 12 |
| Q2.3 | s2 | site-invariant features adversarial MRI multi-site | 702 | 25 |
| Q2.3 | openalex | site-invariant features adversarial MRI multi-site | 1491 | 25 |
| Q2.4 | pubmed | nonlinear site effects harmonization deep learning residual | 3 | 3 |
| Q2.4 | arxiv | all:harmonization AND all:nonlinear AND all:site | 59 | 25 |
| Q2.4 | s2 | nonlinear site effects harmonization deep learning residual | 248 | 25 |
| Q2.4 | openalex | nonlinear site effects harmonization deep learning residual | 3514 | 25 |
| Q2.5 | pubmed | domain adversarial scanner invariance medical imaging | 5 | 5 |
| Q2.5 | arxiv | all:adversarial AND all:scanner AND all:invariant | 11 | 11 |
| Q2.5 | s2 | domain adversarial scanner invariance medical imaging | 1964 | 25 |
| Q2.5 | openalex | domain adversarial scanner invariance medical imaging | 949 | 25 |
| Q3.0 | pubmed | causal effect estimation learned representations confounding adjustment images | 3 | 3 |
| Q3.0 | arxiv | all:causal AND all:confounding AND all:image AND all:representation | 32 | 25 |
| Q3.0 | s2 | causal effect estimation learned representations confounding adjustment images | 57 | 25 |
| Q3.0 | openalex | causal effect estimation learned representations confounding adjustment images | 3696 | 25 |
| Q3.1 | pubmed | text as confounder adjustment representation causal | 3 | 3 |
| Q3.1 | arxiv | all:"text as" AND all:confounder | 362 | 25 |
| Q3.1 | s2 | text as confounder adjustment representation causal | 274 | 25 |
| Q3.1 | openalex | text as confounder adjustment representation causal | 26107 | 25 |
| Q3.2 | pubmed | deep learning confounder adjustment imaging observational causal effect bias | 0 | 0 |
| Q3.2 | arxiv | all:confounder AND all:imaging AND all:"causal effect" | 25 | 25 |
| Q3.2 | s2 | deep learning confounder adjustment imaging observational causal effect bias | 110 | 25 |
| Q3.2 | openalex | deep learning confounder adjustment imaging observational causal effect bias | 13616 | 25 |
| Q3.3 | pubmed | residual confounding embeddings causal inference | 1 | 1 |
| Q3.3 | arxiv | all:embeddings AND all:confounding AND all:causal | 72 | 25 |
| Q3.3 | s2 | residual confounding embeddings causal inference | 595 | 25 |
| Q3.3 | openalex | residual confounding embeddings causal inference | 13300 | 25 |
| Q3.4 | pubmed | harmonization site confounding causal inference neuroimaging | 1 | 1 |
| Q3.4 | arxiv | all:harmonization AND all:causal AND all:confounding | 5 | 5 |
| Q3.4 | s2 | harmonization site confounding causal inference neuroimaging | 230 | 25 |
| Q3.4 | openalex | harmonization site confounding causal inference neuroimaging | 877 | 25 |
| Q3.5 | pubmed | video representations confounding adjustment causal | 0 | 0 |
| Q3.5 | arxiv | all:video AND all:confounding AND all:causal | 50 | 25 |
| Q3.5 | s2 | video representations confounding adjustment causal | 160 | 25 |
| Q3.5 | openalex | video representations confounding adjustment causal | 6453 | 25 |
| Q4.0 | pubmed | bias amplification instrumental variable time-varying treatment | 1 | 1 |
| Q4.0 | arxiv | all:"bias amplification" | 121 | 25 |
| Q4.0 | s2 | bias amplification instrumental variable time-varying treatment | 1154 | 25 |
| Q4.0 | openalex | bias amplification instrumental variable time-varying treatment | 31105 | 25 |
| Q4.1 | pubmed | Z-bias longitudinal adjustment | 1 | 1 |
| Q4.1 | arxiv | all:"Z-bias" | 17 | 17 |
| Q4.1 | s2 | Z-bias longitudinal adjustment | 7360 | 25 |
| Q4.1 | openalex | Z-bias longitudinal adjustment | 489274 | 25 |
| Q4.2 | pubmed | bias amplification marginal structural model | 0 | 0 |
| Q4.2 | arxiv | all:"bias amplification" AND all:longitudinal | 1 | 1 |
| Q4.2 | s2 | bias amplification marginal structural model | 1730 | 25 |
| Q4.2 | openalex | bias amplification marginal structural model | 113705 | 25 |
| Q4.3 | pubmed | conditioning on instrument time-varying confounding bias | 0 | 0 |
| Q4.3 | arxiv | all:instrument AND all:"time-varying" AND all:confounding AND all:bias | 4 | 4 |
| Q4.3 | s2 | conditioning on instrument time-varying confounding bias | 171 | 25 |
| Q4.3 | openalex | conditioning on instrument time-varying confounding bias | 78421 | 25 |
| Q4.4 | pubmed | adjustment for instrumental variables increases bias sequential treatments | 0 | 0 |
| Q4.4 | arxiv | all:"instrumental variable" AND all:adjustment AND all:bias AND all:sequential | 1 | 1 |
| Q4.4 | s2 | adjustment for instrumental variables increases bias sequential treatments | 86 | 25 |
| Q4.4 | openalex | adjustment for instrumental variables increases bias sequential treatments | 28203 | 25 |
| Q4.5 | pubmed | multicenter study center as instrument bias amplification | 0 | 0 |
| Q4.5 | arxiv | all:center AND all:instrument AND all:"bias amplification" | 0 | 0 |
| Q4.5 | s2 | multicenter study center as instrument bias amplification | 72 | 25 |
| Q4.5 | openalex | multicenter study center as instrument bias amplification | 7663 | 25 |
| Q1.100 | pubmed | concept erasure held-out generalization protected attribute recovered | 0 | 0 |
| Q1.100 | arxiv | all:erasure AND all:"protected attribute" | 3 | 3 |
| Q1.100 | s2 | concept erasure held-out generalization protected attribute recovered | 0 | 0 |
| Q1.100 | openalex | concept erasure held-out generalization protected attribute recovered | 1036 | 25 |
| Q1.101 | pubmed | debiasing word embeddings protected attribute still recoverable classifier | 0 | 0 |
| Q1.101 | arxiv | all:debiasing AND all:recoverable | 0 | 0 |
| Q1.101 | s2 | debiasing word embeddings protected attribute still recoverable classifier | 1 | 1 |
| Q1.101 | openalex | debiasing word embeddings protected attribute still recoverable classifier | 320 | 25 |
| Q1.102 | pubmed | fair representation transfer distribution shift protected attribute leakage | 0 | 0 |
| Q1.102 | arxiv | all:"fair representation" AND all:shift | 5 | 5 |
| Q1.102 | s2 | fair representation transfer distribution shift protected attribute leakage | 7 | 7 |
| Q1.102 | openalex | fair representation transfer distribution shift protected attribute leakage | 6547 | 25 |
| Q1.103 | pubmed | linear guardedness | 1 | 1 |
| Q1.103 | arxiv | all:guardedness | 27 | 25 |
| Q1.103 | s2 | linear guardedness | 4937344 | 25 |
| Q1.103 | openalex | linear guardedness | 37550 | 25 |
| Q2.100 | pubmed | ComBat residual site effects detectable classifier | 1 | 1 |
| Q2.100 | arxiv | all:ComBat AND all:classifier | 219 | 25 |
| Q2.100 | s2 | ComBat residual site effects detectable classifier | 1527 | 25 |
| Q2.100 | openalex | ComBat residual site effects detectable classifier | 9936 | 25 |
| Q2.101 | pubmed | site prediction accuracy after ComBat harmonization | 3 | 3 |
| Q2.101 | arxiv | all:"site prediction" | 75 | 25 |
| Q2.101 | s2 | site prediction accuracy after ComBat harmonization | 2599 | 25 |
| Q2.101 | openalex | site prediction accuracy after ComBat harmonization | 6613 | 25 |
| Q2.102 | pubmed | nonlinear batch effects machine learning detect scanner after harmonization | 0 | 0 |
| Q2.102 | arxiv | all:"batch effects" AND all:scanner | 5 | 5 |
| Q2.102 | s2 | nonlinear batch effects machine learning detect scanner after harmonization | 4 | 4 |
| Q2.102 | openalex | nonlinear batch effects machine learning detect scanner after harmonization | 583 | 25 |
| Q2.103 | pubmed | scanner identification deep learning features harmonized | 7 | 7 |
| Q2.103 | arxiv | all:scanner AND all:identification AND all:harmonized | 2 | 2 |
| Q2.103 | s2 | scanner identification deep learning features harmonized | 20190 | 25 |
| Q2.103 | openalex | scanner identification deep learning features harmonized | 5517 | 25 |
| Q3.100 | pubmed | harmonization causal effect estimation bias multi-site | 0 | 0 |
| Q3.100 | arxiv | all:harmonization AND all:"causal effect" | 5 | 5 |
| Q3.100 | s2 | harmonization causal effect estimation bias multi-site | 260 | 25 |
| Q3.100 | openalex | harmonization causal effect estimation bias multi-site | 6414 | 25 |
| Q3.101 | pubmed | batch effects causal inference confounding | 9 | 9 |
| Q3.101 | arxiv | all:"batch effects" AND all:causal | 2 | 2 |
| Q3.101 | s2 | batch effects causal inference confounding | 2495 | 25 |
| Q3.101 | openalex | batch effects causal inference confounding | 12117 | 25 |
| Q3.102 | pubmed | pretrained representations confounding adjustment causal effect | 2 | 2 |
| Q3.102 | arxiv | all:"pre-trained representations" AND all:confounding | 2 | 2 |
| Q3.102 | s2 | pretrained representations confounding adjustment causal effect | 3223 | 25 |
| Q3.102 | openalex | pretrained representations confounding adjustment causal effect | 2270 | 25 |
| Q3.103 | pubmed | image embeddings residual confounding treatment effect | 2 | 2 |
| Q3.103 | arxiv | all:"image" AND all:"treatment effect" AND all:confounding AND all:embedding | 4 | 4 |
| Q3.103 | s2 | image embeddings residual confounding treatment effect | 5313 | 25 |
| Q3.103 | openalex | image embeddings residual confounding treatment effect | 17989 | 25 |
| Q4.100 | pubmed | Z-bias time-varying treatment | 0 | 0 |
| Q4.100 | arxiv | all:"Z-bias" AND all:"time-varying" | 0 | 0 |
| Q4.100 | s2 | Z-bias time-varying treatment | 4653 | 25 |
| Q4.100 | openalex | Z-bias time-varying treatment | 871916 | 25 |
| Q4.101 | pubmed | bias amplification time-varying treatment | 2 | 2 |
| Q4.101 | arxiv | all:"bias amplification" AND all:"time-varying" | 0 | 0 |
| Q4.101 | s2 | bias amplification time-varying treatment | 3683 | 25 |
| Q4.101 | openalex | bias amplification time-varying treatment | 251127 | 25 |
| Q4.102 | pubmed | incremental propensity score intervention bias amplification instrument | 0 | 0 |
| Q4.102 | arxiv | all:"incremental propensity score" | 10 | 10 |
| Q4.102 | s2 | incremental propensity score intervention bias amplification instrument | 79 | 25 |
| Q4.102 | openalex | incremental propensity score intervention bias amplification instrument | 2441 | 25 |
| Q4.103 | pubmed | modified treatment policy instrumental variable adjustment bias | 1 | 1 |
| Q4.103 | arxiv | all:"modified treatment policy" | 25 | 25 |
| Q4.103 | s2 | modified treatment policy instrumental variable adjustment bias | 866 | 25 |
| Q4.103 | openalex | modified treatment policy instrumental variable adjustment bias | 41430 | 25 |
| Q4.104 | pubmed | adjusting for instruments g-computation inverse probability weighting time-varying bias | 0 | 0 |
| Q4.104 | arxiv | all:instrument AND all:"g-computation" | 0 | 0 |
| Q4.104 | s2 | adjusting for instruments g-computation inverse probability weighting time-varying bias | 37 | 25 |
| Q4.104 | openalex | adjusting for instruments g-computation inverse probability weighting time-varying bias | 10120 | 25 |
| Q4.id:2411.14285 | arxiv | id_list=2411.14285 | 1 | 1 |
| Q4.id:2609.11222 | arxiv | id_list=2609.11222 | 1 | 1 |

## Files

All in `/srv/ss_exploratory/literature/`:

* `search.py` and `search2.py`: the two search rounds;
* `query_log.csv`: the query log;
* `records_raw.jsonl`: every stored record, with question and query id;
* `raw/`: the API responses;
* `build_report.py`: checks the quotes, identifiers, years and venues, and writes this report.
