# ss_exploratory

**SS-DS203 exploratory analyses X1 / X2.** Exploratory analyses X1 / X2 (outside the frozen protocol; plan registered on OSF before launch, https://osf.io/5c627): plan, implementation notes, code, tests, records, and the literature check.

Part of the code and records of the manuscript *Semi-synthetic evaluation of site information and linear erasure in clinical video representations for sequentially doubly robust causal effect estimation* (Nakano H, Shiinoki T; article DOI: [TO FILL]). The six repositories of this release are archived together, as git bundles at tag `v1.0.0-submission`, on Zenodo: https://doi.org/10.5281/zenodo.23934337.

Repositories of this release:

* [`medical_video_causal_gate`](https://github.com/repro-analysis-archive/medical_video_causal_gate)
* [`ss_exploratory`](https://github.com/repro-analysis-archive/ss_exploratory)
* [`ss_exploratory_B`](https://github.com/repro-analysis-archive/ss_exploratory_B)
* [`step7_prep`](https://github.com/repro-analysis-archive/step7_prep)
* [`jbi_figures_tables`](https://github.com/repro-analysis-archive/jbi_figures_tables)
* [`ss-ds203-records`](https://github.com/repro-analysis-archive/ss-ds203-records)

Release: tag `v1.0.0-submission` (2026-11-04).

## Contents

`EXPLORATORY_PLAN_X1_X2.md`, `X_IMPLEMENTATION_NOTES.md`, `xplore/` (code), `run_x.sh`, `tests/`, `results_X/` (records), `osf/` (registration package), `literature/` (search scripts, query log, notes, `fulltext/MANIFEST.json`).

## Commit identifiers cited in the manuscript (Supplementary Methods) and records

Each identifier can be checked with `git show <ID>` in a clone of this repository.

| meaning | original ID (cited in the Supplementary Methods / records) | ID in this repository |
|---|---|---|
| X1 / X2 plan | `b6d1cf7` (`b6d1cf7893bff97cd17775f2c4807654ad545781`) | `b6d1cf7893bff97cd17775f2c4807654ad545781` (unchanged) |
| X1 / X2 test logs and launch | `015595d` (`015595dd7f7ecffab7c116bc76ba4ba8c790843b`) | `f23f7033f9e78e001f0507c19602d59f2631d35a` |
| X1 / X2 records | `1c8e628` (`1c8e628ef5d3f0b228a10ba43b0ff17bc0fd96d0`) | `fa0648f0ac6d7c24ac94fd28a9728219f8335694` |

## History filtering and commit identifiers

This repository is a filtered copy of the original history (`git filter-repo`): `literature/raw/` (187 raw API responses) and `literature/records_raw.jsonl` were removed from the whole history because some abstract fields contain third-party text fragments and the responses carry third-party e-mail addresses (decision D2). 8 commits → 8; the plan commit `b6d1cf7` precedes the removed files and keeps its ID, the 7 later commits get new IDs. The OSF registration (2026-10-13) predates `015595d` and `1c8e628` and contains neither. `literature/search.py` / `search2.py` re-create the removed inputs from the public APIs (results may differ); `build_notes.py` and `build_report.py` need them. Commit messages and dates are unchanged, so messages still name original IDs.

* `COMMIT_ID_MAP.md` — original → public ID of every commit;
* `removed_paths.txt` — the exact paths removed from the whole history;
* `FILTER_RECORD.md` — tool, command and the checks performed when the copy was built (2026-10-28).

The unfiltered original history is not distributed (it contains the removed third-party material). It is kept by the authors as a git bundle (SHA-256 `475a506d51beb45a12b7b5d2cfa519e398f79fc6f77450ae472cb4515b89639b`) so that the original identifiers can be verified; requests to the corresponding author.

## Not included

* video files and per-frame representations of Appendix300
* literature full texts (never tracked; `literature/fetch_fulltext.py` re-retrieves them from `fulltext/MANIFEST.json`)
* `literature/raw/` and `literature/records_raw.jsonl` (see *History filtering*)

Scripts and records contain absolute paths of the machines on which the analysis ran (for example `/home/user/…`, `/srv/…`, `/media/user/LaCie/…`, `/Volumes/ADDATA/…`). They are recorded as they were; adapt them to re-run.

## Data source and attribution

The video data are Appendix300 (CC BY 4.0), used with attribution (manuscript references 1 and 45):

* Kolbinger FR, Kirchner M, Pfeiffer K, Bodenstedt S, Jenke AC, Barthel J, et al. Appendix300: Surgical video and patient metadata of 330 laparoscopic appendectomy cases from five institutions [dataset]. Technische Universität Dresden, OPARA; 2026-04-29. doi:10.25532/OPARA-1173. License: CC BY 4.0.
* Kolbinger FR, Kirchner M, Pfeiffer K, Bodenstedt S, Jenke AC, Barthel J, et al. Appendix300: Surgical video and patient metadata of 330 laparoscopic appendectomy cases from five institutions. Sci Data. 2026;13:886. doi:10.1038/s41597-026-07593-6.

No video file, video frame or per-frame representation is redistributed here.

## Licence

* **Original code** (`xplore/`, `tests/`, `run_x.sh`, `literature/*.py`): MIT License — see `LICENSE`. Copyright (c) 2026 Hisashi Nakano.
* **Records, results and figure data** (the plan, notes, `results_X/`, `osf/` and the literature notes): Creative Commons Attribution 4.0 International (CC BY 4.0) — see `LICENSE-CC-BY-4.0`.
* **Not covered by either licence:** third-party material quoted or embedded in this repository remains under its own terms (quotations of bibliographic records in the literature notes).

## How to cite

Please cite the article (DOI: [TO FILL]) and the Zenodo archive https://doi.org/10.5281/zenodo.23934337; machine-readable metadata: `CITATION.cff`.

## Use of AI tools

Most commits carry a `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` line: code and records were produced with Claude Code under the investigator's instructions, as declared in the manuscript. Automated record commits made by the runners carry no such line. The lines are kept unchanged.

## Authors and contact

* Hisashi Nakano (ORCID [0000-0002-9023-880X](https://orcid.org/0000-0002-9023-880X)), Department of Health Data Science, Niigata University of Health and Welfare — hisashi-nakano@nuhw.ac.jp (corresponding)
* Takehiro Shiinoki (ORCID [0000-0002-0246-8489](https://orcid.org/0000-0002-0246-8489)), Department of Radiation Oncology, Yamaguchi University
