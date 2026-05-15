import asyncio
import json
import threading
from datetime import date
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from supervisor import supervisor_state, start_pipeline_run, cancel_pipeline_run
import config

app = FastAPI(title="AutoNews AI Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

output_dir = config.BASE_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(output_dir)), name="media")


@app.on_event("startup")
def on_startup():
    try:
        from database import init_database
        init_database()
    except Exception as e:
        print(f"[WARN] DB init failed: {e}")


# ========================== PIPELINE ==========================

@app.get("/api/pipeline/status")
def get_status():
    from supervisor import get_supervisor_state
    return get_supervisor_state()


@app.post("/api/pipeline/start")
def start_pipeline(background_tasks: BackgroundTasks):
    if supervisor_state.is_running:
        return {"status": "error", "message": "Pipeline is already running."}
    thread = threading.Thread(
        target=start_pipeline_run,
        kwargs={"max_videos": 1, "auto_upload": False},
        daemon=True,
    )
    thread.start()
    return {"status": "started", "message": "Pipeline started."}


@app.post("/api/pipeline/cancel")
def cancel_pipeline():
    cancel_pipeline_run()
    return {"status": "cancel_requested"}


# ========================== LOGS ==========================

@app.get("/api/logs/stream")
async def stream_logs(request: Request):
    async def log_generator():
        last_index = 0
        while True:
            if await request.is_disconnected():
                break
            current_logs = supervisor_state.get_logs()
            if len(current_logs) > last_index:
                for log_item in current_logs[last_index:]:
                    yield f"data: {json.dumps(log_item)}\n\n"
                last_index = len(current_logs)
            await asyncio.sleep(0.5)
    return StreamingResponse(log_generator(), media_type="text/event-stream")


# ========================== CONTENT QUEUE ==========================

@app.get("/api/content/queue")
def get_queue():
    queue_file = Path(config.DATA_DIR) / "approval_queue.json"
    if queue_file.exists():
        try:
            return json.loads(queue_file.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


@app.post("/api/content/approve/{item_id}")
def approve_item(item_id: str):
    queue_file = Path(config.DATA_DIR) / "approval_queue.json"
    if not queue_file.exists():
        raise HTTPException(status_code=404, detail="Queue not found")
    try:
        queue = json.loads(queue_file.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read queue")
    item = next((q for q in queue if q.get("id") == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    def do_upload():
        try:
            from pipeline import approve_and_upload
            approve_and_upload(item_id)
        except Exception as e:
            print(f"[ERROR] Approve upload failed: {e}")

    threading.Thread(target=do_upload, daemon=True).start()
    return {"status": "upload_started", "id": item_id}


@app.delete("/api/content/queue/{item_id}")
def reject_item(item_id: str):
    queue_file = Path(config.DATA_DIR) / "approval_queue.json"
    if not queue_file.exists():
        raise HTTPException(status_code=404, detail="Queue not found")
    try:
        queue = json.loads(queue_file.read_text(encoding="utf-8"))
        new_queue = [q for q in queue if q.get("id") != item_id]
        queue_file.write_text(
            json.dumps(new_queue, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {"status": "removed", "id": item_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================== STATS ==========================

@app.get("/api/stats")
def get_stats():
    total_videos = 0
    videos_today = 0
    last_run = None

    state_file = Path(config.DATA_DIR) / "pipeline_state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            total_videos = state.get("total_videos", 0)
            last_run = state.get("last_run")
            today_str = date.today().isoformat()
            for run in state.get("runs", []):
                if run.get("timestamp", "").startswith(today_str):
                    videos_today += run.get("successful", 0)
        except Exception:
            pass

    pending_count = 0
    queue_file = Path(config.DATA_DIR) / "approval_queue.json"
    if queue_file.exists():
        try:
            queue = json.loads(queue_file.read_text(encoding="utf-8"))
            pending_count = sum(
                1 for item in queue if item.get("status") == "pending_approval"
            )
        except Exception:
            pass

    return {
        "videos_today": videos_today,
        "total_videos": total_videos,
        "pending_approval": pending_count,
        "last_run": last_run,
        "is_running": supervisor_state.is_running,
    }


# ========================== DB ==========================

@app.get("/api/db/stats")
def get_db_stats():
    try:
        from database import db
        return db.get_pipeline_stats()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/db/logs")
def get_db_logs(limit: int = 50, agent: str = None):
    try:
        from database import db
        return db.get_recent_logs(limit=limit, agent=agent)
    except Exception as e:
        return {"error": str(e)}
