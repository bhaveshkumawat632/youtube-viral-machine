import json

from modules import state_manager


def test_state_lifecycle_and_unique_ids(tmp_path, monkeypatch):
    state_file = tmp_path / "queue.json"
    monkeypatch.setattr(state_manager, "STATE_FILE", str(state_file))

    first = state_manager.create_job("first", source="test")
    second = state_manager.create_job("second", source="test")
    assert first != second

    state_manager.update_job_step(first, "rendering", {"asset": "scene.mp4"})
    current = json.loads(state_file.read_text())
    assert current[first]["status"] == "processing"
    assert current[first]["step"] == "rendering"
    assert current[first]["data"]["asset"] == "scene.mp4"

    state_manager.mark_job_complete(first)
    state_manager.mark_job_failed(second, "QA failed")
    final = json.loads(state_file.read_text())
    assert final[first]["status"] == "complete"
    assert final[first]["step"] == "complete"
    assert final[second]["status"] == "failed"
    assert final[second]["error"] == "QA failed"


def test_recover_stale_jobs_preserves_recent_work(tmp_path, monkeypatch):
    state_file = tmp_path / "queue.json"
    monkeypatch.setattr(state_manager, "STATE_FILE", str(state_file))
    state_file.write_text(json.dumps({
        "old_pending": {
            "status": "pending", "step": "audio_visuals", "created_at": 100.0
        },
        "old_processing": {
            "status": "processing", "step": "assembling", "updated_at": 200.0
        },
        "recent": {
            "status": "processing", "step": "rendering", "updated_at": 950.0
        },
        "done": {"status": "complete", "step": "complete", "updated_at": 10.0},
    }))

    recovered = state_manager.recover_stale_jobs(max_age_seconds=100, now=1000)
    assert recovered == ["old_pending", "old_processing"]

    final = json.loads(state_file.read_text())
    assert final["old_pending"]["status"] == "failed"
    assert final["old_pending"]["step"] == "audio_visuals"
    assert "recovered as stale" in final["old_pending"]["error"]
    assert final["recent"]["status"] == "processing"
    assert final["done"]["status"] == "complete"
