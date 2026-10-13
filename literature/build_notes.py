"""Build RELATED_WORK_NOTES.md (CC_TASK_SS_exploratory_followup_v1.md §3).

Every reference must match a stored record (records_raw.jsonl) by title; every identifier, year and venue shown
must occur in those records. References seen only in a retrieved full text's reference list are checked as exact
text on that page and are flagged as not retrieved.

    python build_notes.py
"""
import json
import os
import re
import sys

import fulltext_check as F

HERE = os.path.dirname(os.path.abspath(__file__))
RECS = [json.loads(l) for l in open(os.path.join(HERE, "records_raw.jsonl"))]

EXT = "extension of prior work"
NF = "not found in the searched literature"

# reference: (record key in LIT_CHECK or "", title regex, year, venue, ids, what it shows)
POINTS = [
    dict(
        head="1. Instrument adjustment and bias amplification (single time point)",
        refs=[
            ("Q4-b", r"^On a Class of Bias-Amplifying Variables", "2012", "arXiv (Cornell University)",
             {"doi": "10.48550/arxiv.1203.3503"},
             "Conditioning on instruments amplifies unmeasured-confounding bias. This extends to nonlinear models "
             "less sweepingly, and can create bias where none existed."),
            ("Q4-c", r"^Reducing Bias Amplification in the Presence of Unmeasured Confounding", "2014",
             "Journal of Causal Inference", {"doi": "10.1515/jci-2014-0009", "pmid": "25313347"},
             "Controlling for predictors of treatment (instruments and measured confounders) amplifies the bias "
             "from unmeasured confounders; DRS-based mitigation."),
            ("", r"^Principles of confounder selection", "2019", "European Journal of Epidemiology",
             {"doi": "10.1007/s10654-019-00494-6", "pmid": "30840181"},
             "A practical rule: control for causes of exposure or outcome, but exclude any variable known to be an "
             "instrument."),
            ("Q4-d", r"^Causal Simulation Experiments: Lessons from Bias Amplification", "2020", "arXiv",
             {"arxiv": "2003.08449"},
             "Simulations in clinical settings suggest the amplification is often smaller in practice than "
             "theory suggests."),
            ("Q4-e", r"^Modeling Versus Balancing Approaches to Addressing Instrumental Variables", "2025",
             "Pharmacoepidemiology and Drug Safety", {"doi": "10.1002/pds.70173", "pmid": "40576288"},
             "Instruments in propensity-score weighting affect bias and precision and can cause practical "
             "positivity violations."),
            ("Q4-f", r"^Bias amplification of unobserved confounding in pharmacoepidemiological", "2023",
             "Pharmacoepidemiology and Drug Safety", {"doi": "10.1002/pds.5614", "pmid": "36919941"},
             "Restricting the sample on a treatment predictor (indication) can amplify unobserved-confounding "
             "bias."),
            ("Q4-g", r"^Optimal Covariate Adjustment beyond the Average Treatment Effect", "2026", "arXiv",
             {"arxiv": "2609.11222"},
             "For weighted estimands with propensity-dependent weights (e.g., overlap weights), instrument "
             "adjustment changes the estimand itself (\"estimand drift\")."),
        ],
        unretrieved=[
            "Myers JA, Rassen JA, Gagne JJ, Huybrechts KF, Schneeweiss S, Rothman KJ, et al. Effects of adjusting "
            "for instrumental variables on Bias and precision of effect estimates. Am J Epidemiol. "
            "2011;174:1213–22.",
            "Ding P, Vanderweele TJ, Robins JM. Instrumental variables as bias amplifiers with general outcome and "
            "confounding. Biometrika. 2017;104:291–302.",
            "Pearl J. Invited commentary: understanding Bias amplification. Am J Epidemiol. 2011;174:1223–7.",
            "Wooldridge JM. Should instrumental variables be used as matching variables? Res Econ. "
            "2016;70:232–7.",
        ],
        relation=[
            (EXT, "Our with/without-centre (C) contrasts ask whether this phenomenon appears when the "
                  "instrument-like variable is a centre, in a sequential design (§2)."),
        ],
    ),
    dict(
        head="2. Longitudinal extension",
        refs=[
            ("Q4-a", r"^Bias amplification in the g-computation algorithm for time-varying treatments", "2022",
             "BMC Medical Research Methodology", {"doi": "10.1186/s12874-022-01563-3", "pmid": "35468735"},
             "Full text checked (`FULLTEXT_CHECK.md`):\n"
             "    * the setting is two time points, static regimes and parametric g-computation;\n"
             "    * adjusting for a perfect time-fixed instrument raised the bias by about +0.3 percentage points "
             "on 4–6 points of baseline bias (N = 200,000);\n"
             "    * the effect reversed for near-instruments tied to the unmeasured confounder (β1 ≥ 0.1)."),
        ],
        relation=[
            (EXT, "Instrument adjustment amplifying bias under time-varying treatment is already shown, for generic "
                  "instruments and static regimes. Our results bear on it only as an extension."),
            (NF, "A centre variable as the instrument-like covariate in sequential adjustment."),
            (NF, "Instrument-like adjustment in a modified treatment policy (or an incremental/stochastic "
                 "intervention)."),
            (NF, "Instrument-like adjustment with a sequential doubly robust estimator."),
            (NF, "Instrument-like information carried implicitly by learned representations."),
        ],
    ),
    dict(
        head="3. Site harmonization and residual site information",
        refs=[
            ("Q2-a", r"^Removing the effects of the site in brain imaging machine-learning", "2022", "NeuroImage",
             {"doi": "10.1016/j.neuroimage.2022.119800", "pmid": "36481413"},
             "ComBat removes simple site effects (enough for lasso) but leaves complex effects that can bias SVM "
             "predictions."),
            ("Q2-b", r"^Mitigating site effects in covariance for machine learning", "2021", "Human Brain Mapping",
             {"doi": "10.1002/hbm.25688", "pmid": "34904312"},
             "Removing site effects in mean and variance may not be enough for ML, because site also lives in the "
             "covariance."),
            ("Q2-c", r"^DeepComBat", "2024", "Human Brain Mapping", {"doi": "10.1002/hbm.26708", "pmid": "39056477"},
             "Significant multivariate batch effects remain after state-of-the-art harmonization."),
            ("Q2-d", r"^Machine Learning with Multi-Site Imaging Data: An Empirical Study", "2019", "arXiv",
             {"arxiv": "1910.04597"},
             "A classifier identifies data origin with very high accuracy after pre-processing; harmonization does "
             "not remove scanner bias."),
            ("Q2-e", r"^Failure to Achieve Domain Invariance With Domain Generalization", "2023", "IEEE Access",
             {"doi": "10.1109/ACCESS.2023.3268704"},
             "Domain-generalization training leaves substantial domain information in medical-imaging features."),
            ("Q2-k", r"^Dataset-Specific Encoding of Image Content Underlies Cross-Dataset Failure", "2026", "arXiv",
             {"arxiv": "2610.13027"},
             "LEACE/INLP removal of dataset signal from brain-MRI foundation-model features does not improve "
             "transfer (preprint)."),
            ("Q2-x1", r"^Deep feature batch correction using ComBat", "2024", "Journal of Pathology Informatics",
             {"doi": "10.1016/j.jpi.2024.100396", "pmid": "39398947"},
             "Contrary: ComBat on pathology foundation-model embeddings brought an attention-MIL site probe to "
             "about chance."),
            ("Q2-x2", r"^Cross.Scanner Harmonization of Neuromelanin", "2021", "Journal of Magnetic Resonance Imaging",
             {"doi": "10.1002/jmri.27679", "pmid": "33960063"},
             "Contrary: after ComBat, SVM scanner classification was at chance."),
        ],
        relation=[
            (EXT, "Site remaining decodable by nonlinear probes after linear removal is established in medical "
                  "imaging. Our MLP result after LEACE (step 5, 278-case set: BA P 0.957, S 0.495, REF 0.863) is a "
                  "new instance, in surgical-video foundation-model embeddings. The contrary records show the "
                  "outcome is not universal."),
        ],
    ),
    dict(
        head="4. Linear concept erasure and its limits",
        refs=[
            ("", r"^LEACE: Perfect linear concept erasure in closed form", "2023", "Neural Information Processing Systems",
             {"arxiv": "2306.03819", "doi": "10.52202/075280-2884"},
             "Closed-form erasure that provably prevents all linear classifiers from detecting the concept (the "
             "method we use)."),
            ("", r"^Null It Out", "2020", "Annual Meeting of the Association for Computational Linguistics",
             {"arxiv": "2004.07667", "doi": "10.18653/v1/2020.acl-main.647"},
             "INLP: iterative nullspace projection."),
            ("", r"^Linear Adversarial Concept Erasure", "2022", "International Conference on Machine Learning",
             {"arxiv": "2201.12091"}, "R-LACE: linear minimax concept erasure."),
            ("", r"^Better Hit the Nail on the Head", "2022", "Conference on Empirical Methods in Natural Language Processing",
             {"arxiv": "2212.04273"}, "Mean projection (MP) as a single targeted projection."),
            ("Q2-f", r"^Adversarial Removal of Demographic Attributes from Text Data", "2018",
             "Conference on Empirical Methods in Natural Language Processing",
             {"arxiv": "1808.06640", "doi": "10.18653/v1/D18-1002"},
             "A post-hoc classifier recovers attributes after adversarial removal."),
            ("Q2-g", r"^(Kernelized Concept Erasure|Adversarial Concept Erasure in Kernel Space)", "2022",
             "Conference on Empirical Methods in Natural Language Processing",
             {"arxiv": "2201.12191", "doi": "10.18653/v1/2022.emnlp-main.405"},
             "Protection against one nonlinear adversary does not transfer to others."),
            ("Q2-h", r"^Obliviator Reveals the Cost of Nonlinear Guardedness", "2026",
             "The Thirty-Ninth Annual Conference on Neural Information Processing Systems 2025", {"arxiv": "2603.07529"},
             "Existing erasure methods remain vulnerable to nonlinear adversaries. (OpenAlex gives year 2026 and "
             "the venue as NeurIPS 2025; check before citing.)"),
            ("Q2-j", r"(Log-)?linear Guardedness and its Implications", "2023",
             "Annual Meeting of the Association for Computational Linguistics (ACL)",
             {"arxiv": "2210.10012", "doi": "10.18653/v1/2023.acl-long.523"},
             "A downstream multiclass log-linear model can recover a linearly erased concept indirectly."),
            ("Q1-a", r"^A framework for analyzing concept representations in neural models", "2026",
             "Conference on Computational Natural Language Learning",
             {"arxiv": "2605.01381", "doi": "10.18653/v1/2026.conll-main.34"},
             "Full text checked: LEACE leaks on held-out data under linear probes (Table 5: 29.6 % phones, 54.4 % "
             "speakers vs best cases 7.8 / 2.7)."),
            ("Q1-b", r"^Detecting a Shift Is Not Enough", "2026", "arXiv", {"arxiv": "2610.08069"},
             "Full text checked: finite-calibration linear erasers (MP, SAL, LEACE) leave a predictable share of "
             "a device shift in new participants, and remove only first-moment differences (preprint)."),
            ("Q1-c", r"^Impossibility results for fair representations", "2021", "arXiv", {"arxiv": "2107.03483"},
             "Full text checked: no fixed representation keeps demographic-parity fairness under every change of "
             "the marginal, including the uniform distribution over a subset (theory, worst case)."),
            ("Q2-x3", r"^Adversarial Removal of Demographic Attributes Revisited", "2019",
             "Conference on Empirical Methods in Natural Language Processing", {"doi": "10.18653/v1/D19-1662"},
             "Caution: leakage detected after removal may not generalize to new samples."),
        ],
        relation=[
            (EXT, "Nonlinear recovery after linear erasure, and LEACE's guarantee failing on held-out data, are "
                  "established. Our MLP result after LEACE is a further instance."),
            (NF, "A linear eraser fitted on a cohort (278 cases; linear site BA 0.250 = chance for 4 centres) "
                 "failing on a prespecified, window-selected subset of that same cohort (158 cases; BA 0.393–0.448). "
                 "Q1-c gives a worst-case existence argument that such subsets can exist, but no record shows it "
                 "for a natural selection rule."),
        ],
    ),
    dict(
        head="5. Representation adjustment in causal inference",
        refs=[
            ("", r"^Adapting Text Embeddings for Causal Inference", "2019",
             "Conference on Uncertainty in Artificial Intelligence", {"arxiv": "1905.12741"},
             "Causally sufficient low-dimensional embeddings of text used for adjustment."),
            ("", r"^Text and Causal Inference: A Review", "2020",
             "Annual Meeting of the Association for Computational Linguistics (ACL)",
             {"arxiv": "2005.00649", "doi": "10.18653/v1/2020.acl-main.474"},
             "Review of using text to remove confounding."),
            ("", r"^Estimating Causal Effects Under Image Confounding Bias", "2022", "arXiv", {"arxiv": "2206.06410"},
             "Conditions for identification and estimation when images carry the confounding."),
            ("Q3-a", r"^Adjustment for Confounding using Pre-Trained Representations", "2025",
             "International Conference on Machine Learning", {"arxiv": "2506.14329"},
             "Conditions for valid ATE adjustment with pretrained features. Additive or sparse linear nuisance "
             "assumptions are unrealistic for latent features."),
            ("Q3-d", r"^Reading Between the Lines: Deconfounding Causal Estimates", "2026", "arXiv",
             {"arxiv": "2601.01511"},
             "Tree-based DML retains substantial bias with embeddings; neural nuisances reduce it (synthetic, "
             "preprint)."),
            ("Q3-b", r"^The Confounder Trap: Treatment-Encoding Representations", "2026", "arXiv",
             {"arxiv": "2607.26309"},
             "Representations that encode the treatment induce overlap violations (text, preprint)."),
            ("Q3-c", r"^Detecting and Mitigating Treatment Leakage in Text-Based Causal Inference", "2025", "arXiv",
             {"arxiv": "2601.02400"},
             "INLP and other distillation remove treatment-predictive text before adjustment (preprint)."),
            ("Q3-e", r"^Causal Inference with Video Features as Treatments", "2026", "arXiv", {"arxiv": "2607.06126"},
             "Learned video representations inside a sequential stochastic-intervention estimator, with video "
             "features as the treatment (preprint)."),
        ],
        relation=[
            (EXT, "Adjusting for learned representations, and the dependence on the nuisance-learner class (X2: "
                  "linear vs MLP nuisances), are covered by prior work. Our sequential MTP with SDR on surgical-video "
                  "foundation-model embeddings extends it."),
            (NF, "The consequence for a causal estimate of site information left in representations after erasure "
                 "or harmonization, in a single-time or sequential design. Whether our step 6, X1 or X2 show such "
                 "a consequence is not yet known."),
        ],
    ),
]


def match(pat):
    rs = [r for r in RECS if re.search(pat, r.get("title") or "", re.I)]
    if not rs:
        sys.exit(f"no stored record for {pat!r}")
    return rs


def verify(ref):
    key, pat, year, venue, ids, _ = ref
    rs = match(pat)
    for f, v in ids.items():
        have = {str(r.get(f)).lower() for r in rs if r.get(f)}
        if str(v).lower() not in have:
            sys.exit(f"{pat}: {f}={v} not in stored records {sorted(have)}")
    if year not in {str(r.get("year")) for r in rs}:
        sys.exit(f"{pat}: year {year} not in stored records")
    if venue not in {str(r.get("venue")) for r in rs}:
        sys.exit(f"{pat}: venue {venue!r} not in stored records")
    return max((r["title"] for r in rs), key=len)


def fmt_ids(ids):
    lab = {"doi": "DOI", "pmid": "PMID", "arxiv": "arXiv"}
    return "; ".join(f"{lab[f]} {ids[f]}" for f in ("doi", "pmid", "arxiv") if f in ids)


def main():
    bmc_p10 = F.page_text("s12874-022-01563-3.txt", 10)
    L = []
    w = L.append
    w("# Related-work notes for the manuscript (Introduction and Discussion)")
    w("")
    w("* **Task:** `CC_TASK_SS_exploratory_followup_v1.md` §3. Written 2026-10-13, without any step-6 result.")
    w("* **Sources of every reference:**")
    w("  * every identifier, year and venue comes from the stored API records (`records_raw.jsonl`), checked by "
      "`build_notes.py`;")
    w("  * descriptions come from the abstracts quoted in `LIT_CHECK_ERASURE.md`, or from the full texts in "
      "`FULLTEXT_CHECK.md` where marked \"Full text checked\";")
    w("  * record keys (Q4-a …) refer to `LIT_CHECK_ERASURE.md`.")
    w("* **Labels:**")
    w(f"  * **{EXT}**: prior work shows the phenomenon, and our study extends it to a new setting.")
    w(f"  * **{NF}**: not found in the 166 queries in four indexes, read at abstract level plus four full texts. "
      "This is not a claim that it has never been done; never write \"first\".")
    w("* **Our results:**")
    w("  * The only results cited are the committed step-5 E3 values, as recorded in `EXPLORATORY_PLAN_X1_X2.md`.")
    w("  * Step-6, X1 and X2 results do not exist here. Statements about them describe what the study examines, "
      "not what it found.")
    w("")
    n_refs = 0
    for pt in POINTS:
        w(f"## {pt['head']}")
        w("")
        w("**References (verified):**")
        w("")
        for ref in pt["refs"]:
            title = verify(ref)
            n_refs += 1
            key, _, year, venue, ids, what = ref
            k = f"[{key}] " if key else ""
            w(f"* {k}*{title.rstrip('.')}*. {venue}, {year}. {fmt_ids(ids)}.")
            if "\n" in what:
                head, *rest = what.split("\n")
                w(f"  * {head}")
                for line in rest:
                    w(line.replace("    * ", "    * ", 1))
            else:
                w(f"  * {what}")
        for u in pt.get("unretrieved", []):
            if F.norm(u) not in bmc_p10:
                sys.exit(f"reference-list text not found on Q4-a p.10: {u[:60]!r}")
        if pt.get("unretrieved"):
            w("")
            w("**Not retrieved by our searches.** These appear in the reference list of Q4-a (PDF p. 10), copied "
              "verbatim. They have no stored record or identifier; retrieve and check each before citing it:")
            w("")
            for u in pt["unretrieved"]:
                w(f"* {u}")
        w("")
        w("**How our study relates:**")
        w("")
        for lab, txt in pt["relation"]:
            w(f"* *{lab}*: {txt}")
        w("")
    w("## Claims at a glance")
    w("")
    w("| claim | label | basis |")
    w("|---|---|---|")
    rows = [
        ("Adjusting for an instrument-like variable can amplify bias under time-varying treatment", EXT, "Q4-a (full text)"),
        ("Centre as the instrument-like covariate in a sequential MTP with an SDR estimator", NF, "§2"),
        ("Site remains decodable by nonlinear probes after linear removal", EXT, "Q2-a–e; Q2-f–j (NLP)"),
        ("LEACE's guarantee does not extend to held-out data", EXT, "Q1-a (full text)"),
        ("An eraser fitted on a cohort fails on a prespecified window-selected subset of that cohort", NF, "§4; Q1-c is worst-case theory only"),
        ("Nuisance-learner class matters when adjusting for learned representations", EXT, "Q3-a, Q3-d"),
        ("Residual site information after erasure changes causal estimates", NF, "§5 (our step 6 / X1 / X2 not yet known)"),
    ]
    for c, lab, basis in rows:
        w(f"| {c} | {lab} | {basis} |")
    w("")
    open(os.path.join(HERE, "RELATED_WORK_NOTES.md"), "w").write("\n".join(L))
    print(f"verified {n_refs} references; {sum(len(p.get('unretrieved', [])) for p in POINTS)} reference-list "
          f"entries checked on Q4-a p.10")


if __name__ == "__main__":
    main()
