# FILTER_RECORD — 02 `ss_exploratory`

* Rule: D2 (final): `literature/raw/` (187 files) and `literature/records_raw.jsonl`. Kept: all other literature notes and scripts.
* Tool: git-filter-repo a40bce548d2c (git-filter-repo 2.47.0); `git clone --no-hardlinks <original bundle> repo/`; `git filter-repo --invert-paths --paths-from-file removed_paths.txt --preserve-commit-hashes --force` (log: `filter-repo.log`).
* `repo/` is the filtered repository (clean working tree, no remote, not to be modified before push day; push-day additions are made in a copy). `removed_paths.txt`: exact paths removed from the whole history. `commit-map.raw`: filter-repo's commit map. `COMMIT_ID_MAP.md`: old → new with subjects. `verification.json`: the checks below.

## Checks (all passed)

| check | result |
|---|---|
| commits original → public (pruned / unmapped) | 8 → 8 (0 / 0) |
| `git fsck --full --strict` | exit 0, no output |
| `git log --all -- <every removed path>` | 0 commits |
| `git rev-list --objects --all`: blobs of removed files present / removed path names present | 0 / 0 |
| removed paths ever in the history (blob versions) | 188 (188) |
| HEAD files original → public; only in original | 231 → 43; 188 (all in the removed list: True) |
| HEAD: files only in public / with changed content | 0 / 0 |
| every commit: tree differs from the original tree only by the removed paths | yes (all 8) |
| commit messages and commit / author dates unchanged | yes |
| identities (author \| committer) | Hisashi Nakano <hisashi-nakano@nuhw.ac.jp> | Hisashi Nakano <hisashi-nakano@nuhw.ac.jp> |
| remotes in `repo/` | 0 |
| HEAD original → public | `1c8e628` → `fa0648f` |
