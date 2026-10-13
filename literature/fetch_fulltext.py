"""Retrieve open-access full texts of the key records (CC_TASK_SS_exploratory_followup_v1.md §2).

Only legal open-access routes are used: the PMC open-access XML (NCBI E-utilities), the publisher's PDF for a
BioMed Central (open-access) article, and arXiv abstract pages and PDFs. The licence statement of each source is
saved next to the text. PDFs are converted to text with pdftotext; pages are separated by form feeds.

    python fetch_fulltext.py
"""
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fulltext")
UA = "ss-litcheck/1.0 (mailto:hisashi-nakano@nuhw.ac.jp)"


def get(url, tries=4):
    err = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except Exception as e:                                                             # noqa: BLE001
            err = e
            time.sleep(3 * 2 ** k)
    raise RuntimeError(f"{url}: {err!r}")


def save(name, data):
    p = os.path.join(OUT, name)
    with open(p, "wb") as f:
        f.write(data)
    return dict(file=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def pdf_text(pdf_name, txt_name):
    subprocess.run(["pdftotext", os.path.join(OUT, pdf_name), os.path.join(OUT, txt_name)], check=True)
    data = open(os.path.join(OUT, txt_name), "rb").read()
    return dict(file=txt_name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                pages=data.count(b"\f"))


def bmc(doi, pmid):
    rec = dict(record=f"DOI {doi}", files=[])
    b, _ = get("https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?format=json&ids=" + urllib.parse.quote(doi))
    rec["files"].append(save("pmc_idconv.json", b))
    pmcid = json.loads(b)["records"][0].get("pmcid")
    rec["pmcid"] = pmcid
    if pmcid:
        x, _ = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&retmode=xml&id="
                   + pmcid.replace("PMC", ""))
        rec["files"].append(save(f"{pmcid}.xml", x))
        lic = re.search(rb"<license[^>]*>.*?</license>", x, re.S)
        rec["pmc_license"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", lic.group(0).decode()))[:600] if lic \
            else None
        rec["pmc_license_href"] = (re.search(rb'<license[^>]*xlink:href="([^"]+)"', x) or [None, b""])[1].decode() \
            or None
    time.sleep(1)
    url = f"https://bmcmedresmethodol.biomedcentral.com/counter/pdf/{doi}.pdf"
    p, ct = get(url)
    rec["pdf_url"], rec["pdf_content_type"] = url, ct
    rec["files"].append(save("s12874-022-01563-3.pdf", p))
    rec["files"].append(pdf_text("s12874-022-01563-3.pdf", "s12874-022-01563-3.txt"))
    # Additional file 1 (named in the PMC XML <supplementary-material>), from the publisher's ESM store
    time.sleep(1)
    url = ("https://static-content.springer.com/esm/art%3A10.1186%2Fs12874-022-01563-3/MediaObjects/"
           "12874_2022_1563_MOESM1_ESM.pdf")
    p, ct = get(url)
    rec["supplement_url"], rec["supplement_content_type"] = url, ct
    rec["files"].append(save("12874_2022_1563_MOESM1_ESM.pdf", p))
    rec["files"].append(pdf_text("12874_2022_1563_MOESM1_ESM.pdf", "12874_2022_1563_MOESM1_ESM.txt"))
    return rec


def arxiv(aid):
    rec = dict(record=f"arXiv {aid}", files=[])
    h, _ = get(f"https://arxiv.org/abs/{aid}")
    rec["files"].append(save(f"arxiv_{aid}_abs.html", h))
    s = h.decode("utf-8", "replace")
    m = re.search(r'href="((?:https?:)?//(?:creativecommons\.org|arxiv\.org)/licenses/[^"]+)"', s)
    rec["license_href"] = m.group(1) if m else None
    v = re.findall(rf"/abs/{re.escape(aid)}(v\d+)", s)
    rec["latest_version"] = max(v, key=lambda t: int(t[1:])) if v else None
    time.sleep(3.2)
    url = f"https://arxiv.org/pdf/{aid}{rec['latest_version'] or ''}"
    p, ct = get(url)
    rec["pdf_url"], rec["pdf_content_type"] = url, ct
    rec["files"].append(save(f"arxiv_{aid}.pdf", p))
    rec["files"].append(pdf_text(f"arxiv_{aid}.pdf", f"arxiv_{aid}.txt"))
    time.sleep(3.2)
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    man = [bmc("10.1186/s12874-022-01563-3", "35468735")]
    for aid in ("2605.01381", "2610.08069", "2107.03483"):
        man.append(arxiv(aid))
    json.dump(man, open(os.path.join(OUT, "MANIFEST.json"), "w"), indent=1)
    for r in man:
        print(r["record"], {k: v for k, v in r.items() if k not in ("files", "record")})


if __name__ == "__main__":
    main()
