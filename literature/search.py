"""Focused literature search (CC_TASK_SS_literature_check_erasure_v2.md). Every record comes from a stored API response.

Sources: PubMed (E-utilities esearch + efetch), arXiv (export API), Semantic Scholar (Graph API, key read from
~/.config/s2/key at run time, never printed or stored), OpenAlex (works search). For each (question, query, source):
the hit count reported by the source and up to N records (title, year, venue, identifiers, abstract) are saved;
raw responses go to raw/; the query log to query_log.csv; the merged records to records_raw.jsonl.

    python search.py
"""
import csv
import datetime
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
N = 25
UA = "ss-litcheck/1.0 (mailto:hisashi-nakano@nuhw.ac.jp)"

QUERIES = {
    "Q1": [
        ("concept erasure distribution shift", 'all:"concept erasure" AND all:shift'),
        ("LEACE concept erasure", 'all:LEACE'),
        ("iterative nullspace projection protected attribute removal", 'all:"nullspace projection"'),
        ("linear concept erasure nonlinear recovery", 'all:"concept erasure" AND all:nonlinear'),
        ("adversarial removal demographic attributes recoverable", 'all:"adversarial removal" AND all:attributes'),
        ("concept removal out-of-distribution subgroup", 'all:"concept removal" AND all:distribution'),
    ],
    "Q2": [
        ("ComBat harmonization site classification after harmonization", 'all:ComBat AND all:harmonization AND all:site'),
        ("scanner effects remain after harmonization machine learning", 'all:scanner AND all:harmonization AND all:"machine learning"'),
        ("site information predictable after harmonization MRI", 'all:harmonization AND all:site AND all:predict'),
        ("site-invariant features adversarial MRI multi-site", 'all:"site-invariant"'),
        ("nonlinear site effects harmonization deep learning residual", 'all:harmonization AND all:nonlinear AND all:site'),
        ("domain adversarial scanner invariance medical imaging", 'all:adversarial AND all:scanner AND all:invariant'),
    ],
    "Q3": [
        ("causal effect estimation learned representations confounding adjustment images", 'all:causal AND all:confounding AND all:image AND all:representation'),
        ("text as confounder adjustment representation causal", 'all:"text as" AND all:confounder'),
        ("deep learning confounder adjustment imaging observational causal effect bias", 'all:confounder AND all:imaging AND all:"causal effect"'),
        ("residual confounding embeddings causal inference", 'all:embeddings AND all:confounding AND all:causal'),
        ("harmonization site confounding causal inference neuroimaging", 'all:harmonization AND all:causal AND all:confounding'),
        ("video representations confounding adjustment causal", 'all:video AND all:confounding AND all:causal'),
    ],
    "Q4": [
        ("bias amplification instrumental variable time-varying treatment", 'all:"bias amplification"'),
        ("Z-bias longitudinal adjustment", 'all:"Z-bias"'),
        ("bias amplification marginal structural model", 'all:"bias amplification" AND all:longitudinal'),
        ("conditioning on instrument time-varying confounding bias", 'all:instrument AND all:"time-varying" AND all:confounding AND all:bias'),
        ("adjustment for instrumental variables increases bias sequential treatments", 'all:"instrumental variable" AND all:adjustment AND all:bias AND all:sequential'),
        ("multicenter study center as instrument bias amplification", 'all:center AND all:instrument AND all:"bias amplification"'),
    ],
}


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def get(url, headers=None, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=dict({"User-Agent": UA}, **(headers or {})))
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:                                                             # noqa: BLE001
            err = e
            time.sleep(3 * 2 ** k)
    raise RuntimeError(f"{url[:80]}: {err!r}")


def save(name, data):
    with open(os.path.join(RAW, name), "wb") as f:
        f.write(data)


def pubmed(qid, k, q):
    b = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=%d&term=%s"
            % (N, urllib.parse.quote(q)))
    save(f"pubmed_{qid}_{k}_search.json", b)
    j = json.loads(b)["esearchresult"]
    ids, recs = j.get("idlist", []), []
    if ids:
        time.sleep(0.4)
        x = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id=" + ",".join(ids))
        save(f"pubmed_{qid}_{k}_fetch.xml", x)
        for art in ET.fromstring(x).findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            abst = " ".join("".join(t.itertext()) for t in art.findall(".//Abstract/AbstractText"))
            doi = next((e.text for e in art.findall(".//ArticleId") if e.get("IdType") == "doi"), None)
            recs.append(dict(source="pubmed", pmid=pmid, doi=doi, title="".join(art.find(".//ArticleTitle").itertext()),
                             year=art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate"),
                             venue=art.findtext(".//Journal/Title"), abstract=abst))
    return int(j.get("count", 0)), recs


def arxiv(qid, k, q):
    b = get("http://export.arxiv.org/api/query?start=0&max_results=%d&search_query=%s" % (N, urllib.parse.quote(q)))
    save(f"arxiv_{qid}_{k}.xml", b)
    ns = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/",
          "x": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(b)
    recs = []
    for e in root.findall("a:entry", ns):
        aid = e.findtext("a:id", namespaces=ns).rsplit("/abs/", 1)[-1]
        recs.append(dict(source="arxiv", arxiv=re.sub(r"v\d+$", "", aid), doi=e.findtext("x:doi", namespaces=ns),
                         title=" ".join(e.findtext("a:title", namespaces=ns).split()),
                         year=e.findtext("a:published", namespaces=ns)[:4],
                         venue=e.findtext("x:journal_ref", namespaces=ns) or "arXiv",
                         abstract=" ".join(e.findtext("a:summary", namespaces=ns).split())))
    return int(root.findtext("o:totalResults", namespaces=ns)), recs


def s2(qid, k, q, key):
    b = get("https://api.semanticscholar.org/graph/v1/paper/search?limit=%d&fields=title,abstract,year,venue,"
            "externalIds&query=%s" % (N, urllib.parse.quote(q)), {"x-api-key": key})
    save(f"s2_{qid}_{k}.json", b)
    j = json.loads(b)
    recs = []
    for p in j.get("data", []):
        ex = p.get("externalIds") or {}
        recs.append(dict(source="s2", s2=p.get("paperId"), doi=ex.get("DOI"), pmid=ex.get("PubMed"),
                         arxiv=ex.get("ArXiv"), title=p.get("title"), year=p.get("year"), venue=p.get("venue"),
                         abstract=p.get("abstract") or ""))
    return int(j.get("total", 0)), recs


def openalex(qid, k, q):
    b = get("https://api.openalex.org/works?per-page=%d&search=%s&mailto=hisashi-nakano@nuhw.ac.jp"
            % (N, urllib.parse.quote(q)))
    save(f"openalex_{qid}_{k}.json", b)
    j = json.loads(b)
    recs = []
    for w in j.get("results", []):
        inv = w.get("abstract_inverted_index") or {}
        pos = sorted((i, t) for t, ii in inv.items() for i in ii)
        ids = w.get("ids") or {}
        recs.append(dict(source="openalex", openalex=w.get("id"), doi=(w.get("doi") or "").replace("https://doi.org/", "") or None,
                         pmid=(ids.get("pmid") or "").rsplit("/", 1)[-1] or None, title=w.get("display_name"),
                         year=w.get("publication_year"),
                         venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                         abstract=" ".join(t for _, t in pos)))
    return int(j["meta"]["count"]), recs


def main():
    os.makedirs(RAW, exist_ok=True)
    key = open(os.path.expanduser("~/.config/s2/key")).read().strip()
    log = open(os.path.join(HERE, "query_log.csv"), "w", newline="")
    w = csv.writer(log)
    w.writerow(["time", "question", "query_id", "source", "query", "hits_reported", "records_saved"])
    out = open(os.path.join(HERE, "records_raw.jsonl"), "w")
    for qid, qs in QUERIES.items():
        for k, (plain, ax) in enumerate(qs):
            for src in ("pubmed", "arxiv", "s2", "openalex"):
                q = ax if src == "arxiv" else plain
                try:
                    if src == "pubmed":
                        hits, recs = pubmed(qid, k, q)
                    elif src == "arxiv":
                        hits, recs = arxiv(qid, k, q)
                        time.sleep(3.2)
                    elif src == "s2":
                        hits, recs = s2(qid, k, q, key)
                        time.sleep(1.1)
                    else:
                        hits, recs = openalex(qid, k, q)
                except Exception as e:                                                     # noqa: BLE001
                    w.writerow([now(), qid, f"{qid}.{k}", src, q, f"ERROR {e!r}"[:200], 0])
                    log.flush()
                    continue
                w.writerow([now(), qid, f"{qid}.{k}", src, q, hits, len(recs)])
                log.flush()
                for r in recs:
                    out.write(json.dumps(dict(r, question=qid, query_id=f"{qid}.{k}")) + "\n")
                time.sleep(0.4)
    out.close()
    log.close()


if __name__ == "__main__":
    main()
