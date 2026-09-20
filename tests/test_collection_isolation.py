"""Fresh-process collection isolation with the real conftest bootstrap.

Spawns real `pytest` sessions (via an in-process driver calling pytest.main,
so restoration can be verified after it returns but before process exit) in
disposable synthetic roots using the repository's actual tests/conftest.py
(via symlink, same inode). Covers:
- VIRUSH_RUNTIME_DIR initially unset (child env scrubbed post-merge);
- VIRUSH_RUNTIME_DIR pointing at a caller-owned synthetic directory holding
  nested sentinel files.

Proves the child sees the variable absent before the real conftest bootstrap
executes, collection resolves every mutable path into the exact session-owned
root, caller-owned files stay byte-identical, caller-owned directories survive
process exit, session-owned storage is cleaned, and the incoming environment
value is restored after pytest.main returns. Never touches real user data.
"""

import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_CONFTEST = os.path.join(REPO, "tests", "conftest.py")
SENTINEL = b"caller-owned sentinel content 0123456789"
MUTABLE_ATTRS = (
    "OUTPUT_DIR",
    "ASSETS_DIR",
    "MANIFEST_FILE",
    "FAILED_DIR",
    "LOG_FILE",
    "ALERT_FILE",
)

PROBE_SOURCE = """
import json
import os

import vidrush_pipeline

# Snapshot at COLLECTION time (module import), before any fixture runs:
# these are the values the real conftest bootstrap produced.
_AT_IMPORT_ENV = os.environ.get("VIRUSH_RUNTIME_DIR")
_AT_IMPORT = {name: getattr(vidrush_pipeline, name) for name in %r}
_CALLER = os.environ["YT_VM_CALLER"]
_CHECKOUT = %r


def test_collection_uses_exact_session_root():
    session_dir = _AT_IMPORT_ENV
    assert session_dir, "session env missing at collection time"
    assert session_dir != _CALLER, session_dir
    for name, value in _AT_IMPORT.items():
        assert value == session_dir or value.startswith(
            session_dir + os.sep), (name, value)
        assert not value.startswith(_CALLER + os.sep), (name, value)
        assert not value.startswith(_CHECKOUT + os.sep), (name, value)
    sentinel = os.path.join(_CALLER, "nested", "deep", "sentinel.txt")
    with open(sentinel, "rb") as f:
        assert f.read() == %r
    with open(os.environ["YT_VM_RESULT"], "w") as f:
        json.dump({"session_dir": session_dir, "at_import": _AT_IMPORT}, f)
""" % (MUTABLE_ATTRS, REPO, SENTINEL)

DRIVER_SOURCE = """
import json
import os
import sys

import pytest

# Proves the scrubbed state BEFORE the real conftest bootstrap executes
# (conftest runs at collection, i.e. inside pytest.main below).
pre_absent = "VIRUSH_RUNTIME_DIR" not in os.environ
pre_value = os.environ.get("VIRUSH_RUNTIME_DIR")
expected = os.environ.get("YT_VM_EXPECTED", "<ABSENT>")
if expected == "<ABSENT>":
    assert pre_absent, "child env still carries VIRUSH_RUNTIME_DIR pre-bootstrap"
else:
    assert pre_value == expected, (pre_value, expected)

code = pytest.main(["probe_test.py", "-p", "no:cacheprovider", "-q"])

# pytest.main returned: sessionfinish already ran. Verify restoration now,
# still inside the child process before exit.
post = os.environ.get("VIRUSH_RUNTIME_DIR", "<ABSENT>")
restored_ok = (post == expected)
with open(os.environ["YT_VM_RESTORE"], "w") as f:
    json.dump({"pre_absent": pre_absent, "restored_ok": restored_ok,
               "post_value": post, "pytest_code": code}, f)
sys.exit(code)
"""


def _child_env(unset, overrides):
    """Complete child environment: explicit base, overrides applied, then the
    unset list removed LAST so an inherited value can never leak back in."""
    env = dict(os.environ)
    env.update(overrides)
    for key in unset:
        env.pop(key, None)
    env["PYTHONPATH"] = REPO + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run_session(root, child_env):
    try:
        os.symlink(REAL_CONFTEST, os.path.join(root, "conftest.py"))
    except FileExistsError:
        pass
    with open(os.path.join(root, "probe_test.py"), "w") as f:
        f.write(PROBE_SOURCE)
    with open(os.path.join(root, "run_session.py"), "w") as f:
        f.write(DRIVER_SOURCE)
    completed = subprocess.run(
        [sys.executable, "run_session.py"],
        env=child_env,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=240,
    )
    return completed


def _check_caller_intact(caller_owned):
    assert os.path.isdir(caller_owned), "caller-owned directory did not survive"
    sentinel = os.path.join(caller_owned, "nested", "deep", "sentinel.txt")
    with open(sentinel, "rb") as f:
        assert f.read() == SENTINEL, "caller-owned bytes changed"


def _make_caller_owned(root):
    caller_owned = os.path.join(root, "caller_owned")
    nested = os.path.join(caller_owned, "nested", "deep")
    os.makedirs(nested)
    with open(os.path.join(nested, "sentinel.txt"), "wb") as f:
        f.write(SENTINEL)
    return caller_owned


def test_collection_with_env_unset(tmp_path):
    root = str(tmp_path / "synth_unset")
    os.makedirs(root)
    caller_owned = _make_caller_owned(root)
    child_env = _child_env(
        unset=("VIRUSH_RUNTIME_DIR",),
        overrides={
            "YT_VM_CALLER": caller_owned,
            "YT_VM_RESULT": os.path.join(root, "result.json"),
            "YT_VM_RESTORE": os.path.join(root, "restore.json"),
            "YT_VM_EXPECTED": "<ABSENT>",
        },
    )
    assert "VIRUSH_RUNTIME_DIR" not in child_env
    completed = _run_session(root, child_env)
    assert completed.returncode == 0, completed.stdout[-2000:] + completed.stderr[-2000:]
    with open(os.path.join(root, "result.json")) as f:
        result = json.load(f)
    assert result["session_dir"].startswith(tempfile.gettempdir() + os.sep)
    assert result["session_dir"] != caller_owned
    with open(os.path.join(root, "restore.json")) as f:
        restore = json.load(f)
    assert restore["pre_absent"] is True
    assert restore["restored_ok"] is True, restore
    _check_caller_intact(caller_owned)
    assert not os.path.exists(result["session_dir"]), result["session_dir"]


def test_collection_with_caller_owned_env(tmp_path):
    root = str(tmp_path / "synth_preset")
    os.makedirs(root)
    caller_owned = _make_caller_owned(root)
    child_env = _child_env(
        unset=(),
        overrides={
            "VIRUSH_RUNTIME_DIR": caller_owned,
            "YT_VM_CALLER": caller_owned,
            "YT_VM_RESULT": os.path.join(root, "result.json"),
            "YT_VM_RESTORE": os.path.join(root, "restore.json"),
            "YT_VM_EXPECTED": caller_owned,
        },
    )
    assert child_env["VIRUSH_RUNTIME_DIR"] == caller_owned
    completed = _run_session(root, child_env)
    assert completed.returncode == 0, completed.stdout[-2000:] + completed.stderr[-2000:]
    with open(os.path.join(root, "result.json")) as f:
        result = json.load(f)
    assert result["session_dir"] != caller_owned
    assert result["session_dir"].startswith(tempfile.gettempdir() + os.sep)
    with open(os.path.join(root, "restore.json")) as f:
        restore = json.load(f)
    assert restore["pre_absent"] is False
    assert restore["restored_ok"] is True, restore
    assert restore["post_value"] == caller_owned, restore
    _check_caller_intact(caller_owned)
    assert not os.path.exists(result["session_dir"]), result["session_dir"]
    assert os.path.isdir(caller_owned)
