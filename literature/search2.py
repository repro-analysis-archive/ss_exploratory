"""Second, targeted round (same logging; appends to query_log.csv and records_raw.jsonl)."""
import csv, json, os, time
import search as S

Q2ND = {
    "Q1": [("concept erasure held-out generalization protected attribute recovered", 'all:erasure AND all:"protected attribute"'),
           ("debiasing word embeddings protected attribute still recoverable classifier", 'all:debiasing AND all:recoverable'),
           ("fair representation transfer distribution shift protected attribute leakage", 'all:"fair representation" AND all:shift'),
           ("linear guardedness", 'all:guardedness')],
    "Q2": [("ComBat residual site effects detectable classifier", 'all:ComBat AND all:classifier'),
           ("site prediction accuracy after ComBat harmonization", 'all:"site prediction"'),
           ("nonlinear batch effects machine learning detect scanner after harmonization", 'all:"batch effects" AND all:scanner'),
           ("scanner identification deep learning features harmonized", 'all:scanner AND all:identification AND all:harmonized')],
    "Q3": [("harmonization causal effect estimation bias multi-site", 'all:harmonization AND all:"causal effect"'),
           ("batch effects causal inference confounding", 'all:"batch effects" AND all:causal'),
           ("pretrained representations confounding adjustment causal effect", 'all:"pre-trained representations" AND all:confounding'),
           ("image embeddings residual confounding treatment effect", 'all:"image" AND all:"treatment effect" AND all:confounding AND all:embedding')],
    "Q4": [("Z-bias time-varying treatment", 'all:"Z-bias" AND all:"time-varying"'),
           ("bias amplification time-varying treatment", 'all:"bias amplification" AND all:"time-varying"'),
           ("incremental propensity score intervention bias amplification instrument", 'all:"incremental propensity score"'),
           ("modified treatment policy instrumental variable adjustment bias", 'all:"modified treatment policy"'),
           ("adjusting for instruments g-computation inverse probability weighting time-varying bias", 'all:instrument AND all:"g-computation"')],
}

def main():
    key = open(os.path.expanduser("~/.config/s2/key")).read().strip()
    log = open(os.path.join(S.HERE, "query_log.csv"), "a", newline="")
    w = csv.writer(log)
    out = open(os.path.join(S.HERE, "records_raw.jsonl"), "a")
    for qid, qs in Q2ND.items():
        for k, (plain, ax) in enumerate(qs):
            k2 = 100 + k
            for src in ("pubmed", "arxiv", "s2", "openalex"):
                q = ax if src == "arxiv" else plain
                try:
                    hits, recs = (S.pubmed(qid, k2, q) if src == "pubmed" else S.arxiv(qid, k2, q) if src == "arxiv"
                                  else S.s2(qid, k2, q, key) if src == "s2" else S.openalex(qid, k2, q))
                except Exception as e:  # noqa: BLE001
                    w.writerow([S.now(), qid, f"{qid}.{k2}", src, q, f"ERROR {e!r}"[:200], 0]); log.flush(); continue
                w.writerow([S.now(), qid, f"{qid}.{k2}", src, q, hits, len(recs)]); log.flush()
                for r in recs:
                    out.write(json.dumps(dict(r, question=qid, query_id=f"{qid}.{k2}")) + "\n")
                time.sleep(3.2 if src == "arxiv" else 1.1 if src == "s2" else 0.4)
    # direct identifier look-ups (arXiv id_list), recorded as queries too
    for ids in ("2411.14285", "2609.11222"):
        b = S.get("http://export.arxiv.org/api/query?id_list=" + ids)
        S.save(f"arxiv_idlookup_{ids}.xml", b)
        import xml.etree.ElementTree as ET
        ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
        n = 0
        for e in ET.fromstring(b).findall("a:entry", ns):
            n += 1
            out.write(json.dumps(dict(source="arxiv", arxiv=ids, doi=e.findtext("x:doi", namespaces=ns),
                                      title=" ".join((e.findtext("a:title", namespaces=ns) or "").split()),
                                      year=(e.findtext("a:published", namespaces=ns) or "")[:4], venue="arXiv",
                                      abstract=" ".join((e.findtext("a:summary", namespaces=ns) or "").split()),
                                      question="Q4", query_id=f"Q4.id:{ids}")) + "\n")
        w.writerow([S.now(), "Q4", f"Q4.id:{ids}", "arxiv", f"id_list={ids}", n, n]); log.flush()
        time.sleep(3.2)
    out.close(); log.close()

if __name__ == "__main__":
    main()
