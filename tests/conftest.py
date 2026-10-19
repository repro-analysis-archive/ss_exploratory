"""Shared fixtures: a locked-code snapshot of the main repository's step-7 record commit (git archive, read only) and
the locked PLACEHOLDER inputs. Run with at most 2 CPUs (taskset) and code-lock thread settings."""
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from xplore import common as C  # noqa: E402


@pytest.fixture(scope="session")
def snap(tmp_path_factory):
    d = tmp_path_factory.mktemp("locked_snapshot")
    arch = subprocess.run(["git", "-C", C.MAIN_REPO, "archive", "--format=tar", C.STEP7_RECORD_COMMIT,
                           *C.SNAPSHOT_PATHS], capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(d)], input=arch.stdout, check=True)
    C.use_locked(str(d))
    return str(d)


@pytest.fixture(scope="session")
def ph(snap):
    from ss_benchmark import placeholder, seeds
    rep_set, designs, reps, _, full = placeholder.build(set_names=("primary",))
    root = int(seeds.placeholder_seq("grid-driver", "replicates").generate_state(1)[0])
    return dict(rep_set=rep_set, D=designs["primary"], reps=reps["primary"], full=full, root=root,
                orig={k: reps["primary"][k] for k in ("P-C", "S-C", "REF-C")})


@pytest.fixture(scope="session")
def inp(ph):
    from xplore import x1_erasure
    return x1_erasure.placeholder_inputs(ph["rep_set"], ph["D"])


@pytest.fixture(scope="session")
def x1(ph, inp):
    from xplore import x1_erasure
    return x1_erasure.build_x1({k: ph["full"][k]["R"] for k in ("P", "S", "REF")}, inp)


def locked_step6_shards(ph, out, cells, reps, arms):
    """'Step-6' comparator shards from the locked grid_driver._unit (PLACEHOLDER design, root and features)."""
    from ss_benchmark import grid_driver
    grid_driver._S.update(designs={"primary": ph["D"]}, reps={"primary": ph["reps"]}, root=ph["root"])
    os.makedirs(os.path.join(out, "work", "primary"), exist_ok=True)
    for ci in cells:
        for r in reps:
            grid_driver._unit((out, ("primary", ci, r, tuple(arms), "select")))
    return os.path.join(out, "work", "primary")
