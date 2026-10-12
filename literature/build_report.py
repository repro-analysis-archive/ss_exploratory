"""Build LIT_CHECK_ERASURE.md from the stored API records, checking every quote and identifier against them.

Every quote must be an exact substring of an abstract stored in records_raw.jsonl for a record whose title matches
the entry's title pattern; every identifier, year and venue shown must occur in those same records. Any mismatch
aborts the build.

    python build_report.py
"""
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECS = [json.loads(l) for l in open(os.path.join(HERE, "records_raw.jsonl"))]
ID_FIELDS = ("doi", "pmid", "arxiv")

SETTING = ("our setting: frozen foundation-model embeddings of surgical video from 4 centres, LEACE site erasure, "
           "a window-selected sub-population (158 of 278 cases) and a sequential modified treatment policy")

# (key, question, class, title regex, year, venue, ids, quotes, difference)
ENTRIES = [
    # ---------------- Q1 ----------------
    ("Q1-a", "Q1", "PARTIAL", r"^A framework for analyzing concept representations in neural models", "2026",
     "Conference on Computational Natural Language Learning",
     {"doi": "10.18653/v1/2026.conll-main.34", "arxiv": "2605.01381"},
     ["the state-of-theart concept erasure method, LEACE, performs well on both testing axes, but still struggles to "
      "generalize to unseen data"],
     "Text and speech representations, with failure on unseen data rather than on a selected sub-population or time "
     "window of the fitting population; no causal estimation."),
    ("Q1-b", "Q1", "PARTIAL", r"^Detecting a Shift Is Not Enough", "2026", "arXiv", {"arxiv": "2610.08069"},
     ["Standard linear concept erasers (MP, SAL, LEACE) remove the same calibration difference, so the formula gives, "
      "before fitting, exactly how much shift they leave on fresh data and how much calibration a target requires.",
      "On paired clinical and wearable sleep EEG, where differences between participants act as calibration noise, "
      "the formula predicts the device shift left in new participants"],
     "Finite-sample residual of a device mean shift in new participants after fitting on paired calibration "
     "recordings (EEG), not loss of erasure in a selected sub-population; preprint; no causal estimation."),
    ("Q1-c", "Q1", "PARTIAL", r"^Impossibility results for fair representations", "2021", "arXiv",
     {"arxiv": "2107.03483"},
     ["even the basic goal of achieving label-independent Demographic Parity fairness fails once the marginal data "
      "distribution shifts."],
     "A theoretical result for any fixed representation and fairness of downstream classifiers under marginal "
     "shift, not linear erasure or concept decodability in a sub-population; no causal estimation."),
    # ---------------- Q2 ----------------
    ("Q2-a", "Q2", "DIRECT", r"^Removing the effects of the site in brain imaging machine-learning", "2022",
     "NeuroImage", {"doi": "10.1016/j.neuroimage.2022.119800", "pmid": "36481413"},
     ["current Methods Aiming to Remove the EoS (MAREoS, e.g., ComBat) cannot remove complex EoS (e.g., including "
      "interactions between regions)",
      "ComBat removes all simple EoS as needed for predictions based on simple lasso algorithms, but it leaves "
      "residual complex EoS that may bias the predictions based on standard support vector machine algorithms."],
     "Tabular brain-MRI features and ComBat rather than LEACE on video embeddings; the consequence is studied for "
     "prediction accuracy, not causal estimation, and in the whole sample, not a selected sub-population."),
    ("Q2-b", "Q2", "DIRECT", r"^Mitigating site effects in covariance for machine learning", "2021",
     "Human Brain Mapping", {"doi": "10.1002/hbm.25688", "pmid": "34904312"},
     ["we demonstrate that methods for removing site effects in mean and variance may not be sufficient for ML. "
      "This stems from the fact that such methods fail to address how correlations between measurements can vary "
      "across sites."],
     "Cortical-thickness features with mean/variance (ComBat-type) removal, where site lives in the covariance; "
     "the abstract does not name the probe classes; no causal estimation."),
    ("Q2-c", "Q2", "DIRECT", r"^DeepComBat", "2024", "Human Brain Mapping",
     {"doi": "10.1002/hbm.26708", "pmid": "39056477"},
     ["significant multivariate batch effects remain in the data following harmonization by current "
      "state-of-the-art statistical and deep learning methods"],
     "Brain-MRI cortical thickness harmonised with statistical and deep methods, with residual batch effects "
     "assessed by a battery of machine-learning methods; no LEACE, no sub-population and no causal estimation."),
    ("Q2-d", "Q2", "DIRECT", r"^Machine Learning with Multi-Site Imaging Data: An Empirical Study", "2019", "arXiv",
     {"arxiv": "1910.04597"},
     ["Our results demonstrate that even after careful pre-processing with state-of-the-art neuroimaging pipelines "
      "a classifier can easily distinguish between the origin of the data with very high accuracy.",
      "current approaches to harmonize data are unable to remove scanner-specific bias leading to overly optimistic "
      "performance estimates and poor generalization"],
     "Two brain-MRI studies (2 sources) after pre-processing and harmonisation, not post-hoc linear erasure of "
     "embeddings; the consequence studied is sex classification, not causal estimation."),
    ("Q2-e", "Q2", "DIRECT", r"^Failure to Achieve Domain Invariance With Domain Generalization", "2023",
     "IEEE Access", {"doi": "10.1109/ACCESS.2023.3268704"},
     ["we show that all tested algorithms retain significant amounts of domain-specific information in their "
      "feature representations despite explicit training to remove it."],
     "Domain-generalisation training (invariance learned end to end) on medical image classification, not "
     "post-hoc linear erasure of frozen embeddings; no causal estimation."),
    ("Q2-f", "Q2", "PARTIAL", r"^Adversarial Removal of Demographic Attributes from Text Data", "2018",
     "Conference on Empirical Methods in Natural Language Processing",
     {"doi": "10.18653/v1/D18-1002", "arxiv": "1808.06640"},
     ["while the adversarial component achieves chance-level development-set accuracy during training, a post-hoc "
      "classifier, trained on the encoded sentences from the first part, still manages to reach substantially "
      "higher classification accuracies on the same data."],
     "Text, demographic attributes and adversarial (not linear post-hoc) removal; no imaging, no causal "
     "estimation."),
    ("Q2-g", "Q2", "PARTIAL", r"^(Kernelized Concept Erasure|Adversarial Concept Erasure in Kernel Space)", "2022",
     "Conference on Empirical Methods in Natural Language Processing",
     {"doi": "10.18653/v1/2022.emnlp-main.405", "arxiv": "2201.12191"},
     ["We demonstrate that it is possible to prevent specific non-linear adversaries from predicting the concept. "
      "However, the protection does not transfer to different nonlinear adversaries."],
     "Text (binary gender); shows that erasure guards only against the probe class it targets, here kernel "
     "adversaries; no imaging, no causal estimation."),
    ("Q2-h", "Q2", "PARTIAL", r"^Obliviator Reveals the Cost of Nonlinear Guardedness", "2026",
     "The Thirty-Ninth Annual Conference on Neural Information Processing Systems 2025", {"arxiv": "2603.07529"},
     ["While the goal of concept erasure is protection against all adversaries, existing methods remain vulnerable "
      "to nonlinear ones."],
     "General concept-erasure benchmark (social/demographic attributes), not site in medical video; no causal "
     "estimation."),
    ("Q2-i", "Q2", "PARTIAL", r"^TaCo: Targeted Concept Erasure", "2023", "arXiv", {"arxiv": "2312.06499"},
     ["these methods typically rely on linear classifiers, which leave models vulnerable to non-linear adversaries "
      "capable of recovering sensitive information."],
     "NLP fairness (gender, ethnicity) in final-layer representations; no imaging, no causal estimation."),
    ("Q2-j", "Q2", "PARTIAL", r"(Log-)?linear Guardedness and its Implications", "2023",
     "Annual Meeting of the Association for Computational Linguistics (ACL)",
     {"doi": "10.18653/v1/2023.acl-long.523", "arxiv": "2210.10012"},
     ["we constructively demonstrate that a multiclass log-linear model can be constructed that indirectly recovers "
      "the concept in some cases"],
     "A theoretical NLP result: a downstream multiclass model can recover an erased concept indirectly; no imaging, "
     "no causal estimation."),
    ("Q2-k", "Q2", "PARTIAL", r"^Dataset-Specific Encoding of Image Content Underlies Cross-Dataset Failure", "2026",
     "arXiv", {"arxiv": "2610.13027"},
     ["Frozen features of brain MRI foundation models lose accuracy on new datasets, a failure usually blamed on the "
      "features encoding where each scan came from. We show that the failure lies elsewhere.",
      "removing the dataset signal with INLP, LEACE, CORAL or adversarial training never improves sequence transfer"],
     "Closest setting found (LEACE/INLP on medical-imaging foundation-model features, dataset as the concept), but "
     "the abstract reports transfer of a content label to unseen datasets, not residual dataset decodability; brain "
     "MRI, not video; preprint; no causal estimation."),
    # ---------------- Q2 qualifying / contrary ----------------
    ("Q2-x1", "Q2", "CONTRARY", r"^Deep feature batch correction using ComBat", "2024",
     "Journal of Pathology Informatics", {"doi": "10.1016/j.jpi.2024.100396", "pmid": "39398947"},
     ["Attention-based multiple instance learning models were trained to predict tissue-source site (TSS)",
      "ComBat harmonization significantly reduced the AUROC for TSS prediction, with mean AUROCs dropping to "
      "approximately 0.5 for most models, indicating successful mitigation of batch effects"],
     "Pathology foundation-model patch embeddings with ComBat and a nonlinear (attention-MIL) site probe that falls "
     "to about chance for most extractors: the closest representation setting found, with the opposite outcome; "
     "slides, not video; no causal estimation."),
    ("Q2-x2", "Q2", "CONTRARY", r"^Cross.Scanner Harmonization of Neuromelanin", "2021",
     "Journal of Magnetic Resonance Imaging", {"doi": "10.1002/jmri.27679", "pmid": "33960063"},
     ["In the harmonized CNR, the accuracy of the SVM was at chance level (accuracy = 29.5%; P = 0.8542)."],
     "A low-dimensional regional MRI measure with ComBat, where an SVM no longer detects scanner; no embeddings, "
     "no causal estimation."),
    ("Q2-x3", "Q2", "CONTRARY", r"^Adversarial Removal of Demographic Attributes Revisited", "2019",
     "Conference on Empirical Methods in Natural Language Processing", {"doi": "10.18653/v1/D19-1662"},
     ["the diagnostic classifier generalizes poorly to both new in-domain samples and new domains, indicating that it "
      "relies on correlations specific to their particular data sample."],
     "Text; a methodological caution that residual-decodability findings must hold on new samples, relevant to how "
     "probe results after erasure are evaluated."),
    # ---------------- Q3 ----------------
    ("Q3-a", "Q3", "PARTIAL", r"^Adjustment for Confounding using Pre-Trained Representations", "2025",
     "Proceedings of the 42nd International Conference on Machine Learning, PMLR 267:53557-53580, 2025",
     {"arxiv": "2506.14329"},
     ["We formalize conditions under which these latent features enable valid adjustment and statistical inference "
      "in ATE estimation, demonstrating results along the example of double machine learning.",
      "Common structural assumptions for obtaining fast convergence rates with additive or sparse linear models are "
      "shown to be unrealistic for latent features."],
     "Single-time ATE with double machine learning on pretrained features; residual site information after erasure "
     "is not studied (the linear-model point bears on X2's linear nuisance learners)."),
    ("Q3-b", "Q3", "PARTIAL", r"^The Confounder Trap: Treatment-Encoding Representations", "2026", "arXiv",
     {"arxiv": "2607.26309"},
     ["richer representations can make treated and control documents separable, inducing overlap violations even "
      "when the underlying causal problem satisfies overlap."],
     "Text, with the treatment itself (not a site variable) encoded in the representation; single-time; remedy by "
     "masking before representation learning, not post-hoc erasure."),
    ("Q3-c", "Q3", "PARTIAL", r"^Detecting and Mitigating Treatment Leakage in Text-Based Causal Inference", "2025",
     "arXiv", {"arxiv": "2601.02400"},
     ["Treatment leakage occurs when text intended to capture confounding information also contains signals "
      "predictive of treatment status, thereby inducing post-treatment bias in causal estimates.",
      "we propose four text distillation methods -- similarity-based passage removal, distant supervision "
      "classification, salient feature removal, and iterative nullspace projection -- designed to eliminate "
      "treatment-predictive content while preserving confounder information."],
     "Erasure (including INLP) inside a causal pipeline, but of treatment-predictive text, not site; single-time; "
     "the abstract does not characterise what remains after erasure."),
    ("Q3-d", "Q3", "PARTIAL", r"^Reading Between the Lines: Deconfounding Causal Estimates", "2026", "arXiv",
     {"arxiv": "2601.01511"},
     ["standard tree-based DML estimators retain substantial bias (+24%) due to their inability to model the "
      "continuous topology of embedding manifolds."],
     "The nuisance-learner class changes the bias of adjustment for embeddings (synthetic text, single-time); no "
     "site, no erasure."),
    ("Q3-e", "Q3", "PARTIAL", r"^Causal Inference with Video Features as Treatments", "2026", "arXiv",
     {"arxiv": "2607.06126"},
     ["we first reproduce each video using a deep generative model and leverage the model's internal representations "
      "as learned, low-dimensional summaries of video content for causal estimation. We then establish that the "
      "average potential-outcome trajectory under dynamic stochastic interventions is nonparametrically identified."],
     "Learned video representations inside a sequential stochastic-intervention estimator, but the video features "
     "are the treatment and site/erasure are not studied; entertainment/advertising video, not surgery."),
    ("Q3-f", "Q3", "PARTIAL", r"^Mitigating inter-scanner heterogeneity in brain MRI data", "2025", "NeuroImage",
     {"doi": "10.1016/j.neuroimage.2025.121642", "pmid": "41380987"},
     ["ComBat harmonization effectively corrected the heterogeneity for most BIMs, though it was less successful for "
      "certain BIMs, particularly those related to FC.",
      "when using uncorrected data, mega-analysis yielded an excessive number of significant, but unreliable, "
      "associations"],
     "Associational (not causal) analyses of tabular brain metrics; the downstream consequence is shown for "
     "uncorrected data, not for site left after harmonisation."),
    # ---------------- Q4 ----------------
    ("Q4-a", "Q4", "DIRECT", r"^Bias amplification in the g-computation algorithm for time-varying treatments", "2022",
     "BMC Medical Research Methodology", {"doi": "10.1186/s12874-022-01563-3", "pmid": "35468735"},
     ["Conditioning on instrumental variables (IVs) is known to introduce greater bias when there is unmeasured "
      "confounding in the point-treatment settings",
      "In our simulation study, adjusting for a perfect IV of time-varying treatments in the g-computation algorithm "
      "increased bias due to unmeasured confounding, particularly when the IV had a strong relationship with the "
      "treatment.",
      "this bias amplifying feature was not observed (i.e., bias due to unmeasured confounders decreased) by "
      "adjusting for near-IV when it had a stronger association with the unmeasured confounders"],
     "Generic (near-)instruments simulated for g-computation of time-varying treatment effects (multivariate-normal "
     "setting, physician-payment case study); not a site/centre variable, not a modified treatment policy or "
     "stochastic intervention, and not learned representations."),
    ("Q4-b", "Q4", "PARTIAL", r"^On a Class of Bias-Amplifying Variables", "2012", "arXiv (Cornell University)",
     {"doi": "10.48550/arxiv.1203.3503"},
     ["the bias-amplifying potential of instrumental variables extends over to non-linear models, though not as "
      "sweepingly as in linear models",
      "in non-linear models, conditioning on instrumental variables may introduce new bias where none existed "
      "before"],
     "Single time point, generic instruments; no sequential adjustment, no site, no representations."),
    ("Q4-c", "Q4", "PARTIAL", r"^Reducing Bias Amplification in the Presence of Unmeasured Confounding", "2014",
     "Journal of Causal Inference", {"doi": "10.1515/jci-2014-0009", "pmid": "25313347"},
     ["Both theory and simulations have shown that in the presence of unmeasured confounding, controlling for "
      "variables that affect treatment (both instrumental variables and measured confounders) amplifies the bias "
      "caused by unmeasured confounders."],
     "Single time point, disease-risk-score adjustment; no sequential policy, no site."),
    ("Q4-d", "Q4", "PARTIAL", r"^Causal Simulation Experiments: Lessons from Bias Amplification", "2020", "arXiv",
     {"arxiv": "2003.08449"},
     ["existing simulations of bias amplification in clinical settings have suggested bias amplification may not be "
      "as important in many practical cases as suggested in the theoretical literature"],
     "Single time point with a binary treatment; qualifies the practical size of amplification rather than "
     "extending it to sequential adjustment."),
    ("Q4-e", "Q4", "PARTIAL", r"^Modeling Versus Balancing Approaches to Addressing Instrumental Variables", "2025",
     "Pharmacoepidemiology and Drug Safety", {"doi": "10.1002/pds.70173", "pmid": "40576288"},
     ["Recent work shows that including instrumental variables (IVs), associated with only treatment but not with "
      "the outcome, can impact both the bias and precision of the PS-weighted estimators.",
      "IVs or near-IVs may lead to practical violations of positivity assumptions"],
     "Single-time propensity-score weighting; instruments matter through positivity and precision; no sequential "
     "policy, no site."),
    ("Q4-f", "Q4", "PARTIAL", r"^Bias amplification of unobserved confounding in pharmacoepidemiological", "2023",
     "Pharmacoepidemiology and Drug Safety", {"doi": "10.1002/pds.5614", "pmid": "36919941"},
     ["indication-based sampling in the presence of unobserved confounding can give rise to bias amplification, a "
      "self-inflicted phenomenon where one inflates pre-existing bias through inappropriate covariate control."],
     "Single time point; amplification through restricting the sample on a treatment predictor, which is a "
     "selection mechanism but not a site variable or a sequential policy."),
    ("Q4-g", "Q4", "PARTIAL", r"^Optimal Covariate Adjustment beyond the Average Treatment Effect", "2026", "arXiv",
     {"arxiv": "2609.11222"},
     ["an estimand-drift phenomenon under instrument adjustment"],
     "Single time point; weighted estimands and efficiency, not amplification of unmeasured-confounding bias in "
     "sequential adjustment."),
]

SCREENED = [  # relevant-looking records not classified DIRECT/PARTIAL, with the reason
    ("Q1", r"^Rethinking Fair Representation Learning for Performance-Sensitive Tasks", {"arxiv": "2410.04120"},
     "fair representation learning under distribution shift across medical modalities; the abstract reports no "
     "residual attribute decodability"),
    ("Q1", r"^Graph Fairness Learning under Distribution Shifts", {"doi": "10.1145/3589334.3645508"},
     "in-processing fairness for graph neural networks, not post-hoc erasure"),
    ("Q1", r"^The Medium Is Not the Message: Deconfounding Document", {"doi": "10.18653/v1/2025.emnlp-main.1634"},
     "linear erasure of source/language from document embeddings for similarity tasks; no residual-decodability "
     "or causal claim"),
    ("Q3", r"^When no answer is better than a wrong answer", {"doi": "10.1162/imag_a_00458"},
     "treats batch-effect detection as a causal question; no downstream effect estimation with harmonised data"),
    ("Q3", r"^Harmonization with Flow-based Causal Inference", {"arxiv": "2106.06845"},
     "a counterfactual harmonisation method; no downstream causal effect estimation"),
    ("Q3", r"^Quantifying Confounding Bias in Neuroimaging Datasets", {"arxiv": "1907.04102"},
     "dataset decodable from pooled MRI before any removal; no effect estimation"),
    ("Q3", r"^Deconfounding Scores: Feature Representations", {"arxiv": "2104.05762"},
     "representations that improve overlap without bias; generic, no site or erasure"),
    ("Q4", r"^Stochastic interventions, sensitivity analysis, and optimal transport", {"arxiv": "2411.14285"},
     "retrieved by identifier; bounds for stochastic interventions under unmeasured confounding; the abstract has "
     "no instrument or bias-amplification content"),
    ("Q4", r"^NBER TECHNICAL WORKING PAPER SERIES DO INSTRUMENTAL", {},
     "Semantic Scholar returned no abstract, so no quote can be given; not classified"),
    ("Q4", r"^Instrumental variable analysis to estimate treatment effects: a simulation study showing potential",
     {"doi": "10.1186/s12874-022-01598-6"},
     "hospital as an adjustment covariate in an instrumental-variable analysis; not bias amplification"),
    ("Q4", r"^Using high-dimensional propensity scores to automate confounding control", {"pmid": "22262592"},
     "mentions Z-bias only as a consideration for automated covariate selection"),
]


def match(pattern):
    rs = [r for r in RECS if re.search(pattern, r.get("title") or "", re.I)]
    if not rs:
        sys.exit(f"no record for {pattern!r}")
    return rs


def norm_id(f, v):
    v = str(v)
    return v.lower() if f == "doi" else re.sub(r"v\d+$", "", v)


def check_ids(rs, ids, what):
    for f, v in ids.items():
        have = {norm_id(f, r.get(f)) for r in rs if r.get(f)}
        if norm_id(f, v) not in have:
            sys.exit(f"{what}: {f}={v} not in records ({sorted(have)})")


def provenance(rs):
    return ", ".join(sorted({f"{r['query_id']}/{r['source']}" for r in rs}))


def fmt_ids(ids):
    out = []
    for f in ID_FIELDS:
        if f in ids:
            out.append({"doi": "DOI", "pmid": "PMID", "arxiv": "arXiv"}[f] + " " + ids[f])
    return "; ".join(out) if out else "none returned"


def main():
    n_quotes = 0
    blocks = collections.defaultdict(list)
    for key, q, cls, pat, year, venue, ids, quotes, diff in ENTRIES:
        rs = match(pat)
        check_ids(rs, ids, key)
        if year not in {str(r.get("year")) for r in rs}:
            sys.exit(f"{key}: year {year} not in records")
        if venue not in {str(r.get("venue")) for r in rs}:
            sys.exit(f"{key}: venue {venue!r} not in records")
        abstracts = [r.get("abstract") or "" for r in rs]
        for qt in quotes:
            if not any(qt in a for a in abstracts):
                sys.exit(f"{key}: quote not found verbatim: {qt[:80]!r}")
            n_quotes += 1
        title = max((r["title"] for r in rs), key=len) if key != "Q2-g" else \
            "Kernelized Concept Erasure (arXiv) / Adversarial Concept Erasure in Kernel Space (EMNLP)"
        if key == "Q2-j":
            title = "Log-linear Guardedness and its Implications (also indexed as \"Linear Guardedness and its Implications\")"
        blocks[q].append((key, cls, title, year, venue, ids, quotes, diff, provenance(rs)))
    screened = collections.defaultdict(list)
    for q, pat, ids, why in SCREENED:
        rs = match(pat)
        check_ids(rs, ids, pat)
        screened[q].append((max((r["title"] for r in rs), key=len), str(rs[0].get("year")), ids, why))
    log = list(csv.DictReader(open(os.path.join(HERE, "query_log.csv"))))
    print(f"verified: {len(ENTRIES)} classified records, {n_quotes} quotes, {len(SCREENED)} screened records; "
          f"{len(log)} logged queries; {len(RECS)} stored records")
    open(os.path.join(HERE, "LIT_CHECK_ERASURE.md"), "w").write(render(blocks, screened, log))


VERDICT = {
    "Q1": ("PARTIAL",
           "No retrieved record shows a linear eraser fitted on one population failing to remove the concept in a "
           "selected sub-population or time window of that population. The closest records show weaker or "
           "different things: LEACE struggling to generalise to unseen data (text, speech); an exact minimax "
           "residual of a device shift after MP/SAL/LEACE in new participants (EEG); and an impossibility result "
           "for fair representations under marginal shift."),
    "Q2": ("DIRECT (with contrary evidence)",
           "In brain MRI, several records show that site or scanner remains detectable by machine-learning probes "
           "after ComBat-type harmonisation (mean/variance removal leaves covariance and interaction effects that "
           "an SVM or other ML can use), and that domain-generalisation training leaves domain information in the "
           "features. In NLP, linear and adversarial erasure is repeatedly shown to leave the concept recoverable "
           "by nonlinear probes. **Contrary:** ComBat on pathology foundation-model patch embeddings brought a "
           "nonlinear (attention-MIL) site probe to about chance for most extractors, and ComBat on a regional MRI "
           "measure brought an SVM to chance. No record applies LEACE to site in surgical-video embeddings; the "
           "one LEACE/INLP medical-imaging record (brain-MRI foundation models) reports transfer, not residual "
           "decodability."),
    "Q3": ("PARTIAL",
           "No retrieved record studies how site information left after erasure or harmonisation changes a causal "
           "effect estimate. Related work covers: conditions for valid ATE adjustment with pretrained "
           "representations (including that linear/sparse nuisance models are unrealistic for latent features); "
           "representations that encode the treatment and break overlap (text); INLP used to remove "
           "treatment-predictive text before adjustment; tree-based DML retaining bias with embeddings; learned "
           "video representations in a sequential stochastic-intervention estimator (video features as the "
           "treatment); and false associations from uncorrected scanner effects (associational, not causal)."),
    "Q4": ("DIRECT for generic instruments; NONE for site/centre or MTPs",
           "One record (2022 simulation and case study) shows that adjusting for an instrument of a time-varying "
           "treatment in g-computation amplifies unmeasured-confounding bias, and that near-instruments can reduce "
           "bias when they are associated with the unmeasured confounders. All other amplification records are "
           "single time point. No retrieved record treats a site/centre variable as the instrument-like covariate "
           "in sequential adjustment, and none concerns modified treatment policies, incremental or stochastic "
           "interventions, or instrument-like information carried by learned representations."),
}

QUESTIONS = {
    "Q1": "Does a linear concept eraser (LEACE, INLP, R-LACE, mean projection or similar) fitted on one population "
          "fail to remove the concept in a sub-population or under distribution shift?",
    "Q2": "In medical imaging or site/scanner harmonisation, does site remain decodable after linear removal or "
          "harmonisation, especially by nonlinear probes?",
    "Q3": "Has the consequence of such residual site information for causal effect estimation (confounding "
          "adjustment with learned representations) been studied?",
    "Q4": "Has a site/centre variable behaving like an instrument been studied for bias amplification in "
          "longitudinal / sequential (time-varying treatment) adjustment, beyond the single-time-point case?",
}


def render(blocks, screened, log):
    L = []
    w = L.append
    w("# Literature check: erasure fragility and site in sequential adjustment")
    w("")
    w("* **Task:** `CC_TASK_SS_literature_check_erasure_v2.md`. Run 2026-10-13.")
    w("* **Scope kept:**")
    w("  * nothing under `~/projects/medical_video_causal_gate` and nothing from the step-6 run was touched;")
    w("  * files were written only to `/srv/ss_exploratory/literature/`;")
    w("  * the Semantic Scholar key was read from `~/.config/s2/key` at run time and never printed or stored.")
    w("* **No computation.** Only literature APIs were queried.")
    w("")
    w("## How the search was done")
    w("")
    w(f"* **Sources:** PubMed (E-utilities), arXiv (export API), Semantic Scholar (Graph API) and OpenAlex (works "
      f"search).")
    w(f"* **Queries:** {len(log)} logged (`query_log.csv`).")
    w("  * Round 1: 6 queries per question in each of the 4 sources.")
    w("  * Round 2: 4–5 targeted queries per question in each source, plus 2 arXiv identifier look-ups.")
    w("  * arXiv got a fielded Boolean form of each query; the other sources got the plain text. Both forms are "
      "logged.")
    w(f"* **Records:** up to 25 per query, {len(RECS)} in total (`records_raw.jsonl`). Raw API responses are in "
      "`raw/`.")
    w("* **Screening.** I screened by title after de-duplicating titles, then read the abstracts of the shortlist.")
    w("* **Classification is from abstracts only.**")
    w("  * No full text was read, and no citation chasing was done.")
    w("  * Each quote below is verbatim from an abstract returned by an API. `build_report.py` checks this, and checks "
      "every identifier, year and venue against the stored records.")
    w("  * Abstract text is reproduced as the API returned it, including typos and LaTeX.")
    w("* **What \"hits\" means differs by source:**")
    w("  * PubMed: the esearch count for the query;")
    w("  * arXiv: `totalResults` for the fielded query;")
    w("  * OpenAlex: `meta.count` for its full-text search;")
    w("  * Semantic Scholar: the `total` of its relevance search. This is a very loose count (often the whole "
      "index for common words); treat it as nominal.")
    w("* **Labels:**")
    w("  * DIRECT: shows the same thing in a comparable setting.")
    w("  * PARTIAL: related, but in a different setting (e.g., NLP fairness, single time point).")
    w("  * NONE.")
    w("  * CONTRARY marks records that bear on the question but point the other way; they are reported because "
      "leaving them out would overstate the evidence.")
    w(f"* **Our setting**, the reference for every difference sentence: {SETTING[len('our setting: '):]}.")
    w("")
    w("## Verdicts")
    w("")
    w("| question | verdict | DIRECT | PARTIAL | CONTRARY |")
    w("|---|---|---|---|---|")
    for q in ("Q1", "Q2", "Q3", "Q4"):
        c = collections.Counter(b[1] for b in blocks[q])
        w(f"| {q} | {VERDICT[q][0]} | {c['DIRECT']} | {c['PARTIAL']} | {c['CONTRARY']} |")
    w("")
    for q in ("Q1", "Q2", "Q3", "Q4"):
        w(f"## {q}. {QUESTIONS[q]}")
        w("")
        w(f"**Verdict: {VERDICT[q][0]}.** {VERDICT[q][1]}")
        w("")
        for key, cls, title, year, venue, ids, quotes, diff, prov in blocks[q]:
            w(f"### {key} [{cls}] {title}")
            w("")
            w(f"* **IDs:** {fmt_ids(ids)}")
            w(f"* **Year / venue:** {year}, {venue}")
            w("* **Quote:**")
            for qt in quotes:
                w(f"  > \"{qt}\"")
                w("  >")
            L.pop()
            w(f"* **Differs from our setting:** {diff}")
            w(f"* **Retrieved by:** {prov}")
            w("")
        if screened[q]:
            w(f"**Screened, not classified ({q}):**")
            w("")
            for title, year, ids, why in screened[q]:
                w(f"* *{title}* ({year}; {fmt_ids(ids)}): {why}.")
            w("")
    w("## What remains novel in our results")
    w("")
    w("Below, \"not found\" means not found in the 166 queries and abstracts above. It does not mean the work "
      "has never been done.")
    w("")
    w("The step-6 results are not known; none was read. Every point about consequences for estimation is therefore "
      "an open question here, not a finding.")
    w("")
    w("**1. Erasure that holds in the fitting population but not in a selected sub-population.**")
    w("")
    w("* What we found (committed step-5 record, as quoted in `EXPLORATORY_PLAN_X1_X2.md`):")
    w("  * the protocol LEACE was fitted on the 278-case set, and linear site balanced accuracy there was 0.250, which "
      "is chance for 4 centres;")
    w("  * on the 158-case window-selected analysis region it was 0.393–0.448, and E3-site failed.")
    w("* Literature: no retrieved record shows this. The closest records concern unseen data or new participants "
      "(Q1-a, Q1-b) or marginal shift (Q1-c), not selection of a sub-population by window.")
    w("* **This appears novel as a documented failure mode, and as a caution for any eraser fitted before cohort or "
      "window selection.**")
    w("")
    w("**2. Site still decodable by an MLP after LEACE.**")
    w("")
    w("* What we found: on the 278-case set, MLP balanced accuracy was P 0.957, S 0.495, REF 0.863.")
    w("* Literature: **the phenomenon is not novel.**")
    w("  * Nonlinear recovery after linear or adversarial erasure is established in NLP (Q2-f to Q2-j).")
    w("  * Site left after ComBat-type harmonisation and detectable by ML is established in brain MRI (Q2-a to Q2-d).")
    w("* What is new is the instance: surgical-video foundation-model embeddings with LEACE.")
    w("  * It also contrasts with the pathology-embedding ComBat result (Q2-x1), so residual site after removal "
      "is not universal.")
    w("  * Because of Q2-x3, a residual-decodability claim should rest on held-out probe evaluation.")
    w("")
    w("**3. What residual site information does to a causal estimate.**")
    w("")
    w("* Not found for any design, single-time or sequential.")
    w("* Q3-a and Q3-d support the premise of X2: the nuisance-learner class matters when adjusting for learned "
      "representations. But neither paper involves site or erasure.")
    w("* If step 6, X1 or X2 show an effect of residual site on FM−C bias or coverage, that would be new. Whether "
      "they do is unknown.")
    w("")
    w("**4. Site as an instrument-like covariate in a sequential MTP.**")
    w("")
    w("* Bias amplification from adjusting for instruments of a time-varying treatment is already shown for "
      "g-computation with generic instruments (Q4-a). Any claim must be framed as an extension of it, not as the "
      "first longitudinal demonstration.")
    w("* Not found:")
    w("  * a site/centre variable as the instrument-like covariate;")
    w("  * modified treatment policies or incremental/stochastic interventions;")
    w("  * instrument-like information entering through learned representations.")
    w("")
    w("**Limits of this check.**")
    w("")
    w("* Abstracts only; four indexes; English queries; no citation chasing.")
    w("* Several of the closest records are recent arXiv preprints that have not been peer-reviewed (Q1-b, Q2-k, "
      "Q3-b, Q3-c, Q3-d, Q3-e).")
    w("")
    w("## Query log")
    w("")
    w("Copied from `query_log.csv` (one row per query and source; the time column is omitted).")
    w("")
    w("| query_id | source | query | hits reported | records saved |")
    w("|---|---|---|---:|---:|")
    for r in log:
        qtxt = r["query"].replace("|", "\\|")
        w(f"| {r['query_id']} | {r['source']} | {qtxt} | {r['hits_reported']} | {r['records_saved']} |")
    w("")
    w("## Files")
    w("")
    w("All in `/srv/ss_exploratory/literature/`:")
    w("")
    w("* `search.py` and `search2.py`: the two search rounds;")
    w("* `query_log.csv`: the query log;")
    w("* `records_raw.jsonl`: every stored record, with question and query id;")
    w("* `raw/`: the API responses;")
    w("* `build_report.py`: checks the quotes, identifiers, years and venues, and writes this report.")
    w("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
