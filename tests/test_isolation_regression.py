"""Collection-time + alert-cycle isolation proof with synthetic project roots.

Exercises the REAL vidrush_pipeline import (including its makedirs side
effects) and the REAL create_alert/clear_alert behavior against disposable
synthetic roots — never the operator checkout. Verifies BOTH:
- an existing default-location ALERT.txt with known bytes stays identical;
- an absent default-location ALERT.txt stays absent.
"""

import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENTINEL = b"synthetic pre-existing user alert content 0123456789"

_PROBE = """
import os, sys
sys.path.insert(0, {repo!r})
import importlib.util
spec = importlib.util.spec_from_file_location(
    "vp_under_test", {copied!r})
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)
print("ALERT=" + vp.ALERT_FILE)
print("LOG=" + vp.LOG_FILE)
mode = sys.argv[1]
if mode == "cycle":
    vp.create_alert("synthetic isolation check")
    print("created=" + str(os.path.exists(vp.ALERT_FILE)))
    vp.clear_alert()
    print("cleared=" + str(not os.path.exists(vp.ALERT_FILE)))
elif mode != "import-only":
    raise SystemExit("bad mode: " + mode)
"""


def _run_probe(root, mode, runtime_dir=None):
    copied = os.path.join(root, "vidrush_pipeline.py")
    env = dict(os.environ)
    if runtime_dir is None:
        env.pop("VIRUSH_RUNTIME_DIR", None)
    else:
        env["VIRUSH_RUNTIME_DIR"] = runtime_dir
    script = _PROBE.format(repo=REPO, copied=copied)
    return subprocess.run(
        [sys.executable, "-c", script, mode],
        env=env,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _copy_module(root):
    shutil.copy(
        os.path.join(REPO, "vidrush_pipeline.py"),
        os.path.join(root, "vidrush_pipeline.py"),
    )


def _assert_clean(result, root):
    assert result.returncode == 0, (
        "probe failed: " + result.stderr[-2000:]
    )
    # The probe must never resolve mutable state into the real checkout.
    assert REPO + os.sep not in result.stdout.split("ALERT=")[1].splitlines()[0]


def test_existing_default_alert_survives_collection_and_cycle(tmp_path):
    root = str(tmp_path / "proj_existing")
    os.makedirs(root)
    alert_path = os.path.join(root, "ALERT.txt")
    with open(alert_path, "wb") as f:
        f.write(SENTINEL)
    _copy_module(root)

    # 1. Collection-equivalent import with pure defaults: must not alter it.
    result = _run_probe(root, "import-only")
    _assert_clean(result, root)
    with open(alert_path, "rb") as f:
        assert f.read() == SENTINEL

    # 2. Full alert cycle under isolation: default file still identical.
    redir = os.path.join(root, "redir")
    result = _run_probe(root, "cycle", runtime_dir=redir)
    _assert_clean(result, root)
    assert "created=True" in result.stdout
    assert "cleared=True" in result.stdout
    with open(alert_path, "rb") as f:
        assert f.read() == SENTINEL


def test_absent_default_alert_stays_absent(tmp_path):
    root = str(tmp_path / "proj_absent")
    os.makedirs(root)
    alert_path = os.path.join(root, "ALERT.txt")
    _copy_module(root)

    result = _run_probe(root, "import-only")
    _assert_clean(result, root)
    assert not os.path.exists(alert_path)

    redir = os.path.join(root, "redir")
    result = _run_probe(root, "cycle", runtime_dir=redir)
    _assert_clean(result, root)
    assert "created=True" in result.stdout
    assert "cleared=True" in result.stdout
    assert not os.path.exists(alert_path)
