"""X1 / X2 orchestrator behind run_x.sh (orchestration only; plan §7, §8). Never changes locked code.

Preconditions (refused before anything changes; exit 3):
* this repository (/srv/ss_exploratory) at HEAD == --expect-commit, clean tree (no untracked file either);
* the main repository contains the step-7 record commit (--main-commit, default 2880d73) and its HEAD is that commit
  or a descendant in which nothing under ss_benchmark/, data_audit/lead/out/, results/step5/ or results/step6/
  changed (implementation note N2); ss_benchmark/ at that commit = the SDR commit af56777 (adapter excepted);
* real run: the step-5 files (reps.npz, reps_full_{P,S,REF}.npz, checks.json) match the committed
  step5_manifest.json, and the 14,200 step-6 primary shards of the 71 cells match the committed
  results/step6/shard_sha256.txt.gz (note N3); step 6 complete;
* PLACEHOLDER run: may not write under the real output directory; its "step-6" comparator directory is given;
* no process of an earlier X run alive.
Stages (state.json; each resumable): snapshots (locked code of the step-7 record commit; this repository's code at
--expect-commit) → control C0 → X1 erasure + E3 → X1 units → X2 units → comparison and report → automatic commit of
the records (records only, exactly the record files, parent = --expect-commit) in this repository.
Workers: --workers (18) pinned to CPUs 0..N-1, orchestrator on the rest; code-lock thread settings. Memory guard:
MemAvailable < 5 % of RAM, PSI memory full avg60 ≥ 10 % or run RSS > 80 % of RAM, three consecutive 15-s checks →
stop (resumable); swap-out alone is not a criterion. Unit stages are retried (60 / 300 / 900 s) and stop after three
consecutive failures without progress. --status shows progress counts and resources only.

    python -m xplore.x_orchestrate run --repo REPO --expect-commit SHA --out DIR --workers N [options]
    python -m xplore.x_orchestrate status --out DIR
"""
import argparse
import gzip
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

from .common import (CODELOCK_ENV, DEFAULT_OUT, MAIN_REPO, SDR_COMMIT, SDR_EXEMPT, SNAPSHOT_PATHS, STEP5_DIR,
                     STEP6_OUT, STEP7_RECORD_COMMIT, json_read, json_write, now, sha256_file, union_cells)

PY = "/home/user/miniconda3/bin/python3"
MEM_CAP_FRACTION = 0.80
MEM_AVAIL_MIN = 0.05
PSI_FULL_MAX = 10.0
MAX_FAILS = 3
BACKOFF = tuple(int(x) for x in os.environ.get("SS_X_BACKOFF_S", "60,300,900").split(","))
RES_INTERVAL = int(os.environ.get("SS_X_RES_INTERVAL_S", "600"))
WATCH_INTERVAL = 15
STEP5_CHECKED = ("reps.npz", "reps_full_P.npz", "reps_full_S.npz", "reps_full_REF.npz", "checks.json")
MAIN_FROZEN = ("ss_benchmark/", "data_audit/lead/out/", "results/step5/", "results/step6/")
RECORD_DIR = "results_X"
RECORD_FILES = ("X_REPORT.md", "X_heatmaps.pdf", "x_cell_metrics.csv", "x_comparisons_cells.csv",
                "x_comparisons_groups.csv", "x_pairing_c0.json", "x1_erasure_report.json", "x1_e3.json",
                "x_run_record.json", "x_unit_sha256.txt.gz")
PREFIX = "X1/X2 exploratory records (automated, run_x.sh)"


class Stop(Exception):
    pass


class Refuse(Stop):
    pass


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    if check and r.returncode:
        raise Refuse(f"refused: git -C {repo} {' '.join(args[:3])} failed: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def git_bytes(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    if r.returncode:
        raise Refuse(f"refused: git -C {repo} {' '.join(args[:3])} failed")
    return r.stdout


def meminfo():
    m = {}
    for line in open("/proc/meminfo"):
        k, v = line.split(":", 1)
        m[k] = int(v.split()[0]) * 1024
    return m


def psi_memory():
    try:
        out = {}
        for line in open("/proc/pressure/memory"):
            kind, *fields = line.split()
            out[kind] = float(dict(f.split("=") for f in fields)["avg60"])
        return out
    except (OSError, ValueError, KeyError):
        return None


def tree_rss(root_pid):
    parent, rss = {}, {}
    page = os.sysconf("SC_PAGE_SIZE")
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                st = open(f"/proc/{d}/stat").read()
                f = st[st.rindex(")") + 2:].split()
                parent[int(d)], rss[int(d)] = int(f[1]), int(f[21]) * page
            except (OSError, ValueError, IndexError):
                continue
    keep, todo = {root_pid}, [root_pid]
    while todo:
        p = todo.pop()
        for c, pp in parent.items():
            if pp == p and c not in keep:
                keep.add(c)
                todo.append(c)
    return sum(rss.get(p, 0) for p in keep)


def pressure_reasons(mem, psi, rss, cap):
    """Memory-pressure test (pure function). Swap-out is deliberately not a criterion."""
    reasons = []
    if mem["MemAvailable"] < MEM_AVAIL_MIN * mem["MemTotal"]:
        reasons.append(f"MemAvailable {mem['MemAvailable'] / 2**30:.1f} GiB < {MEM_AVAIL_MIN:.0%} of RAM")
    if psi is not None and psi.get("full", 0.0) >= PSI_FULL_MAX:
        reasons.append(f"PSI memory full avg60 {psi['full']:.1f} % >= {PSI_FULL_MAX:.0f} %")
    if rss > cap:
        reasons.append(f"run resident memory {rss / 2**30:.1f} GiB > cap {cap / 2**30:.1f} GiB")
    return reasons


def unit_counts(out):
    res = {}
    for a in ("X1", "X2"):
        d = os.path.join(out, "units", a)
        res[a] = sum(1 for f in os.listdir(d) if f.endswith(".json")) if os.path.isdir(d) else 0
    return res


class Runner:
    def __init__(self, a):
        self.a = a
        self.repo, self.out = os.path.abspath(a.repo), os.path.abspath(a.out)
        self.logs = os.path.join(self.out, "logs")
        self.locked = os.path.join(self.out, "locked_snapshot")
        self.code = os.path.join(self.out, "x_code")
        self.state_p = os.path.join(self.out, "state.json")
        os.makedirs(self.logs, exist_ok=True)
        self.state = json_read(self.state_p, {}) or {}
        self.lock = threading.RLock()
        self.stopping = threading.Event()
        self.proc = None
        n = os.cpu_count()
        self.cpus = ([int(x) for x in a.cpus.split(",")] if a.cpus else list(range(min(a.workers, n))))
        self.orch_cpus = [c for c in range(n) if c not in self.cpus] or list(range(n))
        self.mem_cap = int(MEM_CAP_FRACTION * meminfo()["MemTotal"])
        self.cells = [int(x) for x in a.cells.split(",")] if a.cells else union_cells()
        self.step6_work = os.path.join(os.path.abspath(a.step6_out), "grid", "work", "primary")

    def log(self, msg):
        line = f"{now()} {msg}"
        with self.lock:
            with open(os.path.join(self.logs, "progress.log"), "a") as f:
                f.write(line + "\n")
        print(line, flush=True)

    def save(self):
        with self.lock:
            json_write(self.state_p, self.state)

    # -- preconditions ------------------------------------------------------------------------------------------------
    def preflight(self):
        a, exp = self.a, self.a.expect_commit
        if self.state.get("status") == "complete":
            raise Refuse("refused: this X run is already complete")
        launch = self.state.get("launch_commit")
        if launch and launch != exp:
            raise Refuse(f"refused: this output directory belongs to launch commit {launch[:12]}, not {exp[:12]}")
        if bool(self.state.get("placeholder", a.placeholder)) != bool(a.placeholder):
            raise Refuse("refused: PLACEHOLDER and real runs cannot share an output directory")
        if a.placeholder and os.path.realpath(self.out).startswith(os.path.realpath(DEFAULT_OUT)):
            raise Refuse("refused: a PLACEHOLDER run may not write to the real X output directory")
        if not a.placeholder and (a.cells or a.max_reps):
            raise Refuse("refused: --cells / --max-reps are for PLACEHOLDER runs only")
        head = git(self.repo, "rev-parse", "HEAD")
        if head != exp:
            raise Refuse(f"refused: HEAD {head[:12]} is not --expect-commit {exp[:12]}")
        dirty = git(self.repo, "status", "--porcelain", "--untracked-files=all")
        if dirty:
            raise Refuse(f"refused: working tree not clean: {dirty.splitlines()[:3]}")
        mc, mh = a.main_commit, git(a.main_repo, "rev-parse", "HEAD")
        git(a.main_repo, "cat-file", "-e", f"{mc}^{{commit}}")
        if mh != mc:
            if subprocess.run(["git", "-C", a.main_repo, "merge-base", "--is-ancestor", mc, mh]).returncode:
                raise Refuse(f"refused: main repository HEAD {mh[:12]} is not the step-7 record commit {mc[:12]} or a "
                             f"descendant of it")
            moved = [f for f in git(a.main_repo, "diff", "--name-only", mc, mh).splitlines()
                     if f.startswith(MAIN_FROZEN)]
            if moved:
                raise Refuse(f"refused: frozen inputs changed in the main repository after {mc[:12]}: {moved[:5]}")
        if not git(a.main_repo, "log", "-1", "--format=%s", mc).startswith("SS §14 step 7 record"):
            raise Refuse(f"refused: {mc[:12]} is not a step-7 record commit")
        changed = set(git(a.main_repo, "diff", "--name-only", SDR_COMMIT, mc, "--", "ss_benchmark").splitlines())
        if changed - SDR_EXEMPT:
            raise Refuse(f"refused: ss_benchmark differs from the SDR commit: {sorted(changed - SDR_EXEMPT)[:5]}")
        if not a.placeholder:
            self.check_real_inputs(mc)
        else:
            missing = [ci for ci in self.cells for r in range(a.max_reps or 1)
                       if not os.path.exists(os.path.join(self.step6_work, f"c{ci:03d}_r{r:04d}.json"))]
            if missing:
                raise Refuse(f"refused: PLACEHOLDER comparator shards missing for cells {sorted(set(missing))[:5]}")
        stray = [int(d) for d in os.listdir("/proc") if d.isdigit() and int(d) != os.getpid() and self._is_ours(d)]
        if stray:
            raise Refuse(f"refused: processes of an earlier X run are still alive: {stray[:5]}")
        return head, mh, sorted(changed)

    def check_real_inputs(self, mc):
        man = json.loads(git_bytes(self.a.main_repo, "show", f"{mc}:results/step5/step5_manifest.json"))
        for f in STEP5_CHECKED:
            p = os.path.join(self.a.step5_dir, f)
            if not os.path.exists(p) or sha256_file(p) != man["files"][f]["sha256"]:
                raise Refuse(f"refused: step-5 file {f} is missing or differs from the committed step5_manifest.json")
        st6 = json_read(os.path.join(self.a.step6_out, "state.json"), {}) or {}
        if st6.get("status") != "complete":
            raise Refuse("refused: step 6 is not complete")
        lines = gzip.decompress(git_bytes(self.a.main_repo, "show", f"{mc}:results/step6/shard_sha256.txt.gz"))
        ref = dict(l.split(" ") for l in lines.decode().splitlines() if l)
        for ci in self.cells:
            for r in range(200):
                key = f"primary/c{ci:03d}_r{r:04d}.json"
                p = os.path.join(self.step6_work, f"c{ci:03d}_r{r:04d}.json")
                if key not in ref or not os.path.exists(p) or sha256_file(p) != ref[key]:
                    raise Refuse(f"refused: step-6 shard {key} missing or differs from the committed shard list")
        self.log(f"inputs verified: {len(STEP5_CHECKED)} step-5 files and {len(self.cells) * 200} step-6 shards "
                 f"match the committed records of {mc[:12]}")

    def _is_ours(self, d):
        try:
            cmd = open(f"/proc/{d}/cmdline", "rb").read().decode(errors="replace").split("\0")
        except OSError:
            return False
        return any(x.startswith(self.out) for x in cmd) and any(
            x in ("xplore.x_units", "xplore.x_stage", "xplore.x_orchestrate") for x in cmd)

    # -- snapshots ----------------------------------------------------------------------------------------------------
    def _archive(self, repo, commit, paths, dest, meta_name):
        meta_p = os.path.join(self.out, meta_name)
        meta = json_read(meta_p)
        if meta and meta.get("commit") == commit and os.path.isdir(dest):
            for rel, h in meta["files"].items():
                if sha256_file(os.path.join(dest, rel)) != h:
                    raise Stop(f"snapshot file changed: {dest}/{rel}")
            return meta
        if os.path.exists(dest):
            shutil.rmtree(dest)
        os.makedirs(dest)
        arch = subprocess.run(["git", "-C", repo, "archive", "--format=tar", commit, *paths], capture_output=True,
                              check=True)
        subprocess.run(["tar", "-x", "-C", dest], input=arch.stdout, check=True)
        files = {os.path.relpath(os.path.join(r, f), dest): sha256_file(os.path.join(r, f))
                 for r, _, fs in os.walk(dest) for f in fs}
        meta = dict(commit=commit, created=now(), files=files)
        json_write(meta_p, meta)
        self.log(f"snapshot of {commit[:12]} ({repo}) created: {len(files)} files")
        return meta

    def snapshots(self):
        self._archive(self.a.main_repo, self.a.main_commit, SNAPSHOT_PATHS, self.locked, "locked_snapshot.json")
        self._archive(self.repo, self.a.expect_commit, ("xplore", "run_x.sh"), self.code, "x_code_snapshot.json")

    # -- monitor ------------------------------------------------------------------------------------------------------
    def resource_line(self, prev):
        v = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        busy, total = sum(v[:8]) - v[3] - v[4], sum(v[:8])
        st = os.stat(self.out)
        dev = os.path.basename(os.path.realpath(f"/sys/dev/block/{os.major(st.st_dev)}:{os.minor(st.st_dev)}"))
        rd = wr = 0
        for line in open("/proc/diskstats"):
            f = line.split()
            if f[2] == dev:
                rd, wr = int(f[5]), int(f[9])
        t, m, psi = time.time(), meminfo(), psi_memory()
        line = None
        if prev:
            dt = t - prev["t"]
            line = (f"RES cpu {100.0 * (busy - prev['busy']) / max(1, total - prev['total']):.0f}% load "
                    f"{os.getloadavg()[0]:.1f} | ram used {(m['MemTotal'] - m['MemAvailable']) / 2**30:.1f} GiB avail "
                    f"{m['MemAvailable'] / 2**30:.1f} GiB | psi mem some/full avg60 "
                    f"{psi['some'] if psi else 'n/a'}/{psi['full'] if psi else 'n/a'} | run_rss "
                    f"{tree_rss(os.getpid()) / 2**30:.1f} GiB (cap {self.mem_cap / 2**30:.1f}) | swap_used "
                    f"{(m['SwapTotal'] - m['SwapFree']) / 2**30:.2f} GiB | disk {dev} read "
                    f"{(rd - prev['rd']) * 512 / dt / 1e6:.1f} MB/s write {(wr - prev['wr']) * 512 / dt / 1e6:.1f} MB/s")
        return line, dict(t=t, busy=busy, total=total, rd=rd, wr=wr)

    def monitor(self):
        _, prev = self.resource_line(None)
        last_res, strikes = time.time(), 0
        while not self.stopping.wait(WATCH_INTERVAL):
            if time.time() - last_res >= RES_INTERVAL:
                line, prev = self.resource_line(prev)
                self.log(line)
                last_res = time.time()
            reasons = pressure_reasons(meminfo(), psi_memory(), tree_rss(os.getpid()), self.mem_cap)
            strikes = strikes + 1 if reasons else 0
            if reasons:
                self.log(f"memory pressure ({'; '.join(reasons)}), strike {strikes}/3")
            if strikes >= 3:
                self.shutdown(f"memory pressure: {'; '.join(reasons)}")
                return

    def shutdown(self, why):
        with self.lock:
            if self.stopping.is_set():
                return
            self.stopping.set()
            self.state["stop_reason"] = why
            self.save()
        self.log(f"shutting down: {why}")
        p = self.proc
        if p is not None and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                p.wait(120)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)

    # -- stages -------------------------------------------------------------------------------------------------------
    def common_args(self):
        args = ["--locked", self.locked, "--out", self.out]
        if self.a.placeholder:
            args += ["--placeholder"]
        return args

    def subrun(self, name, cmd, retry=False, progress=None):
        """Run one stage process (pinned, code-lock threads); with retry, rerun on failure while it progresses."""
        fails, last = 0, progress() if progress else None
        env = dict(os.environ, **CODELOCK_ENV, PYTHONPATH=self.code)
        full = ["taskset", "-c", ",".join(map(str, self.cpus)), PY, "-m", *cmd]
        while True:
            self.log(f"{name}: start (attempt {fails + 1})" + (f"; {last} units present" if progress else ""))
            with open(os.path.join(self.logs, f"{name.split()[0]}.log"), "a") as lf:
                lf.write(f"\n===== {now()} start: {' '.join(full)}\n")
                lf.flush()
                self.proc = subprocess.Popen(full, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=self.code,
                                             start_new_session=True)
                rc = self.proc.wait()
                lf.write(f"===== {now()} exit {rc}\n")
            if self.stopping.is_set():
                raise Stop("interrupted")
            if rc == 0:
                return
            if not retry:
                raise Stop(f"{name}: exit {rc}; see logs/{name.split()[0]}.log")
            n = progress() if progress else 0
            if progress and n > last:
                fails, last = 0, n
            fails += 1
            if fails >= MAX_FAILS:
                raise Stop(f"{name}: {fails} consecutive failures without progress (last exit {rc})")
            wait = BACKOFF[min(fails - 1, len(BACKOFF) - 1)]
            self.log(f"{name}: exit {rc}; retry in {wait} s")
            if self.stopping.wait(wait):
                raise Stop("interrupted")

    def done(self, stage):
        return stage in self.state.get("stages_done", [])

    def mark(self, stage, **info):
        self.state.setdefault("stages_done", []).append(stage)
        self.state.setdefault("stage_info", {})[stage] = dict(finished=now(), **info)
        self.save()
        self.log(f"stage {stage} done")

    def run(self):
        head, mh, changed = self.preflight()
        a = self.a
        self.state.setdefault("launch_commit", a.expect_commit)
        self.state.update(pid=os.getpid(), last_start=now(), status="running", placeholder=bool(a.placeholder))
        self.state.pop("stop_reason", None)
        self.state.setdefault("settings", dict(
            workers=a.workers, worker_cpus=self.cpus, orchestrator_cpus=self.orch_cpus, thread_env=CODELOCK_ENV,
            python=PY, memory_cap_bytes=self.mem_cap, cells=self.cells, max_reps=a.max_reps, n_boot=a.n_boot,
            main_repo=a.main_repo, main_commit=a.main_commit, main_head_at_launch=mh, sdr_commit=SDR_COMMIT,
            ss_benchmark_files_differing_from_sdr_commit=changed, step5_dir=None if a.placeholder else a.step5_dir,
            step6_out=os.path.abspath(a.step6_out),
            memory_guard=dict(mem_available_min_fraction=MEM_AVAIL_MIN, psi_full_avg60_max=PSI_FULL_MAX, strikes=3,
                              interval_s=WATCH_INTERVAL, swap_out_rule=None)))
        self.save()
        os.sched_setaffinity(0, set(self.orch_cpus))
        threading.Thread(target=self.monitor, daemon=True).start()
        self.log(f"preflight passed: HEAD {head[:12]}; clean tree; main repository {mh[:12]} (step-7 record commit "
                 f"{a.main_commit[:12]}); ss_benchmark = SDR commit (except {changed or 'nothing'}); {a.workers} "
                 f"workers on CPUs {self.cpus}; {len(self.cells)} cells" + ("; PLACEHOLDER" if a.placeholder else ""))
        self.snapshots()
        mr = [] if a.max_reps is None else ["--max-reps", str(a.max_reps)]
        cl = [] if not a.cells else ["--cells", a.cells]
        nb = [] if a.n_boot is None else ["--n-boot", str(a.n_boot)]
        s5 = [] if a.placeholder else ["--step5-dir", a.step5_dir]
        if not self.done("c0"):
            self.subrun("c0", ["xplore.x_stage", "c0", *self.common_args(), *s5, "--step6-work", self.step6_work])
            c0 = json_read(os.path.join(self.out, "c0.json"), {})
            if not c0.get("passed"):
                raise Stop("control C0 failed: the X code path does not reproduce the step-6 records")
            self.mark("c0", passed=True)
        if not self.done("x1"):
            self.subrun("x1 erasure and E3", ["xplore.x_stage", "x1", *self.common_args(), *s5, *nb])
            self.mark("x1", features_sha256=sha256_file(os.path.join(self.out, "x1", "x1_features.npz")))
        feats = {"X1": os.path.join(self.out, "x1", "x1_features.npz"),
                 "X2": (os.path.join(a.step5_dir, "reps.npz") if not a.placeholder
                        else os.path.join(self.out, "x2_placeholder_features.npz"))}
        if a.placeholder and not os.path.exists(feats["X2"]):
            self.subrun("x2feat", ["xplore.x_stage", "x2feat", *self.common_args()])
        for an in ("X1", "X2"):
            if not self.done(f"units {an}"):
                if an == "X1" and sha256_file(feats["X1"]) != self.state["stage_info"]["x1"]["features_sha256"]:
                    raise Stop("X1 features changed since the erasure stage")
                self.subrun(f"units {an}", ["xplore.x_units", "--locked", self.locked, "--analysis", an, "--features",
                                            feats[an], "--out", self.out, "--workers", str(a.workers), *cl, *mr,
                                            *(["--placeholder"] if a.placeholder else [])],
                            retry=True, progress=lambda an=an: unit_counts(self.out)[an])
                self.mark(f"units {an}", units=unit_counts(self.out)[an],
                          features=dict(path=feats[an], sha256=sha256_file(feats[an])))
        rec_tmp = os.path.join(self.out, "records")
        if not self.done("compare"):
            meta = self.meta(feats)
            json_write(os.path.join(self.out, "meta.json"), meta)
            self.subrun("compare", ["xplore.x_stage", "compare", *self.common_args(), "--step6-work", self.step6_work,
                                    "--records", rec_tmp, "--meta", os.path.join(self.out, "meta.json"), *cl, *mr,
                                    *nb])
            self.write_run_record(rec_tmp, feats)
            self.mark("compare")
        self.commit(rec_tmp)
        self.state["status"] = "complete"
        self.save()
        self.log("X run complete: records committed in this repository (records only)")

    def meta(self, feats):
        inputs = {f"X features {an}": f"{p} sha256 {sha256_file(p)}" for an, p in feats.items()}
        if not self.a.placeholder:
            inputs.update({f"step-5 {f}": sha256_file(os.path.join(self.a.step5_dir, f)) for f in STEP5_CHECKED})
        return dict(x_commit=self.a.expect_commit, locked_commit=self.a.main_commit, inputs=inputs)

    def write_run_record(self, rec_tmp, feats):
        lines = []
        for an in ("X1", "X2"):
            d = os.path.join(self.out, "units", an)
            for f in sorted(os.listdir(d)):
                if f.endswith(".json"):
                    lines.append(f"{an}/{f} {sha256_file(os.path.join(d, f))}")
        with gzip.GzipFile(os.path.join(rec_tmp, "x_unit_sha256.txt.gz"), "wb", mtime=0) as g:
            g.write(("\n".join(lines) + "\n").encode())
        cd = json_read(os.path.join(self.out, "compare_done.json"), {})
        json_write(os.path.join(rec_tmp, "x_run_record.json"), dict(
            launch_commit=self.a.expect_commit, plan_commit="b6d1cf7893bff97cd17775f2c4807654ad545781",
            settings=self.state["settings"], stages=self.state.get("stage_info"), units=unit_counts(self.out),
            unit_digest=hashlib.sha256("\n".join(lines).encode()).hexdigest(), x_replicates=cd.get("x_replicates"),
            locked_snapshot=json_read(os.path.join(self.out, "locked_snapshot.json"), {}).get("commit"),
            placeholder=bool(self.a.placeholder)))

    def commit(self, rec_tmp):
        dest = os.path.join(self.repo, RECORD_DIR)
        rel = [f"{RECORD_DIR}/{f}" for f in RECORD_FILES]
        if git(self.repo, "rev-parse", "HEAD") != self.a.expect_commit:
            if self.state.get("record_commit") and git(self.repo, "rev-parse", "HEAD") == self.state["record_commit"]:
                return
            raise Stop("HEAD moved during the run; records not committed")
        os.makedirs(dest, exist_ok=True)
        for f in RECORD_FILES:
            shutil.copy2(os.path.join(rec_tmp, f), os.path.join(dest, f))
        got = {l[3:] for l in git(self.repo, "status", "--porcelain", "--untracked-files=all").splitlines()}
        if got != set(rel):
            raise Stop(f"untracked files {sorted(got)[:6]} are not exactly the X records")
        git(self.repo, "add", "--", *rel)
        msg = (f"{PREFIX}: cell metrics, paired comparisons, X1 erasure and E3, control C0; records only"
               + (" [PLACEHOLDER]" if self.a.placeholder else ""))
        git(self.repo, "commit", "-q", "-m", msg)
        new = git(self.repo, "rev-parse", "HEAD")
        files = set(git(self.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", new).splitlines())
        if git(self.repo, "rev-parse", f"{new}^") != self.a.expect_commit or files != set(rel) or \
                git(self.repo, "status", "--porcelain", "--untracked-files=all"):
            raise Stop("record commit verification failed")
        self.state["record_commit"] = new
        self.save()
        self.log(f"records committed: {new} (parent {self.a.expect_commit[:12]}; exactly {len(rel)} files)")


def status(out):
    st = json_read(os.path.join(out, "state.json"), {}) or {}
    pid, alive = st.get("pid"), False
    if pid:
        try:
            alive = "x_orchestrate" in open(f"/proc/{pid}/cmdline").read()
        except OSError:
            alive = False
    cells = (st.get("settings") or {}).get("cells") or []
    M = (st.get("settings") or {}).get("max_reps") or 200
    counts = unit_counts(out)
    lines = [f"runner: {'running (pid %d)' % pid if alive else 'not running'}; state {st.get('status', 'not started')}"
             + (f"; STOPPED: {st['stop_reason']}" if st.get("stop_reason") else "")
             + ("; PLACEHOLDER" if st.get("placeholder") else ""),
             f"stages done: {', '.join(st.get('stages_done', [])) or 'none'}",
             "units: " + ", ".join(f"{a} {n}/{len(cells) * M if cells else '?'}" for a, n in counts.items())]
    try:
        log = open(os.path.join(out, "logs", "progress.log")).read().splitlines()
    except OSError:
        log = []
    res = [x for x in log if " RES " in x]
    lines.append(f"last progress-log entry: {log[-1][:25] if log else 'none'}")
    lines.append(f"resources: {res[-1] if res else 'no sample yet'}")
    if st.get("record_commit"):
        lines.append(f"record commit: {st['record_commit']}")
    print("\n".join(lines))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--repo", required=True)
    r.add_argument("--expect-commit", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, required=True)
    r.add_argument("--cpus")
    r.add_argument("--main-repo", default=MAIN_REPO)
    r.add_argument("--main-commit", default=STEP7_RECORD_COMMIT)
    r.add_argument("--step5-dir", default=STEP5_DIR)
    r.add_argument("--step6-out", default=STEP6_OUT)
    r.add_argument("--placeholder", action="store_true")
    r.add_argument("--cells")
    r.add_argument("--max-reps", type=int)
    r.add_argument("--n-boot", type=int)
    s = sub.add_parser("status")
    s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "status":
        return status(a.out)
    run = Runner(a)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda n, f: threading.Thread(target=run.shutdown, args=(f"interrupted by signal {n}",),
                                                         daemon=True).start())
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    try:
        run.run()
        return 0
    except Refuse as e:
        print(f"{now()} {e}", file=sys.stderr)
        return 3
    except Stop as e:
        run.shutdown(str(e))
        run.state["status"] = "stopped"
        run.save()
        run.log(f"STOP: {run.state.get('stop_reason', e)}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
