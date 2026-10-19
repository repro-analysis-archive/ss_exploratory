"""Runner tests (criterion T8) and the PLACEHOLDER smoke run with interruption and resume (criterion S).

The smoke run is opt-in (a few minutes). It works in a throwaway clone of this repository, writes only to temporary
directories, and deletes them at the end:

    SS_X_SMOKE=1 taskset -c 18,19 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0 \
        /home/user/miniconda3/bin/python3 -m pytest -p no:cacheprovider -s -v tests/test_x_runner.py
"""
import json
import os
import shutil
import subprocess
import time

import pytest

from conftest import REPO, locked_step6_shards

ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0")


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def clone(tmp_path):
    c = tmp_path / "clone"
    git(tmp_path, "clone", "--quiet", "--no-hardlinks", REPO, str(c))
    for k in ("user.name", "user.email"):
        git(c, "config", k, git(REPO, "config", "--get", k))
    return c


def test_t8_refuses_without_expect_commit(tmp_path):
    out = tmp_path / "xo"
    r = subprocess.run(["bash", os.path.join(REPO, "run_x.sh"), "--out", str(out)], capture_output=True, text=True,
                       env=ENV)
    assert r.returncode == 3 and "refused" in r.stderr and not out.exists()


def test_t8_refuses_dirty_tree(tmp_path):
    c = clone(tmp_path)
    (c / "stray.txt").write_text("x")
    out = tmp_path / "xo"
    r = subprocess.run(["bash", str(c / "run_x.sh"), "--expect-commit", git(c, "rev-parse", "HEAD"), "--out", str(out),
                        "--placeholder", "--step6-out", str(tmp_path / "s6"), "--cells", "2", "--max-reps", "1",
                        "--workers", "1", "--cpus", "19"], capture_output=True, text=True, env=ENV)
    log = (out / "logs" / "runner_stdout.log").read_text()
    assert r.returncode == 3 and "working tree not clean" in log
    assert not (out / "state.json").exists()


def test_t8_status_shows_no_estimates(tmp_path):
    out = tmp_path / "xo"
    (out / "logs").mkdir(parents=True)
    (out / "state.json").write_text(json.dumps(dict(status="running", pid=None, settings=dict(cells=[2, 18],
                                                                                              max_reps=3))))
    (out / "logs" / "progress.log").write_text("2026-10-19T00:00:00+09:00 RES cpu 10% load 1.0 | ram used 1 GiB\n")
    r = subprocess.run(["bash", os.path.join(REPO, "run_x.sh"), "--status", "--out", str(out)], capture_output=True,
                       text=True, env=ENV)
    assert r.returncode == 0 and "units: X1 0/6, X2 0/6" in r.stdout
    for w in ("est", "bias", "delta", "Δ", "coverage"):
        assert w not in r.stdout.lower().replace("estim", "")


@pytest.mark.skipif(os.environ.get("SS_X_SMOKE") != "1", reason="opt-in: SS_X_SMOKE=1")
def test_s_smoke_run_interrupt_resume(tmp_path, ph):
    from xplore.x_compare import STEP6_ARMS
    from xplore.x_orchestrate import RECORD_DIR, RECORD_FILES, unit_counts
    c = clone(tmp_path)
    head = git(c, "rev-parse", "HEAD")
    s6, xo = tmp_path / "s6", tmp_path / "xo"
    cells, reps = (2, 15, 18), (0, 1, 2)
    t0 = time.time()
    locked_step6_shards(ph, str(s6 / "grid"), cells, reps, STEP6_ARMS)
    print(f"S0 PLACEHOLDER 'step-6' comparator shards (locked grid_driver._unit): {len(cells) * len(reps)} units in "
          f"{time.time() - t0:.0f} s")
    cmd = ["bash", str(c / "run_x.sh"), "--expect-commit", head, "--out", str(xo), "--workers", "2", "--cpus", "18,19",
           "--placeholder", "--step6-out", str(s6), "--cells", ",".join(map(str, cells)), "--max-reps",
           str(len(reps)), "--n-boot", "200"]
    env = dict(ENV, SS_X_RES_INTERVAL_S="20", SS_X_BACKOFF_S="2,2,2")
    p = subprocess.Popen(cmd, env=env, start_new_session=True)
    t0 = time.time()
    while unit_counts(str(xo))["X1"] < 1:
        assert p.poll() is None, f"runner exited early ({p.returncode}); see {xo}/logs"
        assert time.time() - t0 < 1800
        time.sleep(2)
    stop = subprocess.run(["bash", str(c / "run_x.sh"), "--stop", "--out", str(xo)], capture_output=True, text=True,
                          env=ENV)
    rc = p.wait(600)
    st = json.load(open(xo / "state.json"))
    n_at_stop = unit_counts(str(xo))["X1"]
    status = subprocess.run(["bash", str(c / "run_x.sh"), "--status", "--out", str(xo)], capture_output=True,
                            text=True, env=ENV).stdout
    print(f"S1 interrupted after {time.time() - t0:.0f} s: {stop.stdout.strip()}; runner exit {rc}; state "
          f"{st['status']}; stop reason {st.get('stop_reason')!r}; X1 shards {n_at_stop}; stages done "
          f"{st.get('stages_done')}")
    assert rc == 2 and st["status"] == "stopped" and "interrupted" in st.get("stop_reason", "")
    assert "STOPPED" in status
    t1 = time.time()
    r = subprocess.run(cmd, env=env, timeout=3600)
    st = json.load(open(xo / "state.json"))
    new = git(c, "rev-parse", "HEAD")
    files = set(git(c, "diff-tree", "--no-commit-id", "--name-only", "-r", new).splitlines())
    pc = json.load(open(c / RECORD_DIR / "x_pairing_c0.json"))
    rep = (c / RECORD_DIR / "X_REPORT.md").read_text()
    print(f"S2 resumed: exit {r.returncode} in {time.time() - t1:.0f} s; state {st['status']}; units "
          f"{unit_counts(str(xo))}; record commit {new[:12]} parent {git(c, 'rev-parse', 'HEAD^')[:12]} "
          f"(launch {head[:12]}); {len(files)} files = records: {files == {f'{RECORD_DIR}/{f}' for f in RECORD_FILES}}"
          f"; tree clean: {not git(c, 'status', '--porcelain', '--untracked-files=all')}; C0 passed "
          f"{pc['control_c0']['passed']}; pairing pairs {pc['pairing']['pairs_checked']}")
    assert r.returncode == 0 and st["status"] == "complete" and st["record_commit"] == new
    assert git(c, "rev-parse", "HEAD^") == head and files == {f"{RECORD_DIR}/{f}" for f in RECORD_FILES}
    assert not git(c, "status", "--porcelain", "--untracked-files=all")
    assert unit_counts(str(xo)) == {"X1": 9, "X2": 9}
    assert pc["control_c0"]["passed"] and pc["pairing"]["passed"] and pc["pairing"]["pairs_checked"] == 18
    assert "PLACEHOLDER" in rep and "SUPPORTED" not in rep
    log = (xo / "logs" / "progress.log").read_text()
    assert log.count("preflight passed") == 2 and " RES " in log
    r7 = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r7.returncode == 3 and "already complete" in (xo / "logs" / "runner_stdout.log").read_text()
    print(f"S3 relaunch after completion: exit {r7.returncode} (refused: already complete)")
    for d in (xo, s6, c):
        shutil.rmtree(d)
    print("S4 outputs and clone deleted")
