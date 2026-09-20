import os
import json
import time
import tempfile

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "video_queue_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_state(state):
    state_dir = os.path.dirname(STATE_FILE)
    os.makedirs(state_dir, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".video_queue_", suffix=".tmp", dir=state_dir)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, STATE_FILE)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def create_job(topic, source="reddit"):
    now = time.time()
    job_id = f"job_{time.time_ns()}"
    state = load_state()
    state[job_id] = {
        "status": "pending",
        "topic": topic,
        "source": source,
        "step": "init",
        "created_at": now,
        "updated_at": now,
    }
    save_state(state)
    return job_id

def update_job_step(job_id, step, data=None):
    """
    Updates the current step of the job. 
    Steps: init -> script_done -> audio_done -> visual_done -> mixed -> uploaded -> complete
    """
    state = load_state()
    if job_id not in state:
        return
    
    state[job_id]["step"] = step
    state[job_id]["status"] = "processing"
    state[job_id]["updated_at"] = time.time()
    if data:
        state[job_id]["data"] = state[job_id].get("data", {})
        state[job_id]["data"].update(data)
        
    save_state(state)

def mark_job_failed(job_id, error_msg):
    state = load_state()
    if job_id in state:
        state[job_id]["status"] = "failed"
        state[job_id]["error"] = error_msg
        state[job_id]["failed_at"] = time.time()
        state[job_id]["updated_at"] = state[job_id]["failed_at"]
        save_state(state)

def mark_job_complete(job_id):
    state = load_state()
    if job_id in state:
        state[job_id]["status"] = "complete"
        state[job_id]["step"] = "complete"
        state[job_id]["completed_at"] = time.time()
        state[job_id]["updated_at"] = state[job_id]["completed_at"]
        save_state(state)


def recover_stale_jobs(max_age_seconds=3600, now=None):
    """Fail orphaned in-flight records left behind by an interrupted process.

    Pipeline work is not resumable from the recorded step alone, so leaving an
    old record as pending misrepresents it as queued work.  Recovery preserves
    the last step and records an explicit interruption reason.
    """
    now = time.time() if now is None else float(now)
    cutoff = now - max(0, float(max_age_seconds))
    state = load_state()
    recovered = []

    for job_id, job_info in state.items():
        if job_info.get("status") not in {"pending", "processing"}:
            continue
        last_activity = job_info.get("updated_at", job_info.get("created_at", 0))
        if float(last_activity or 0) >= cutoff:
            continue
        job_info["status"] = "failed"
        job_info["error"] = "Interrupted pipeline run recovered as stale"
        job_info["failed_at"] = now
        job_info["updated_at"] = now
        recovered.append(job_id)

    if recovered:
        save_state(state)
    return recovered

def get_pending_job():
    state = load_state()
    for job_id, job_info in state.items():
        if job_info["status"] in ["pending", "processing"]:
            return job_id, job_info
    return None, None
