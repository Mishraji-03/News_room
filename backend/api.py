import asyncio
import json
import threading
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from supervisor import supervisor_state, start_pipeline_run
import config

app = FastAPI(title="AutoNews AI Pipeline API")

# Allow React app to talk to API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the videos folder so the dashboard can play them
app.mount("/media", StaticFiles(directory=str(config.BASE_DIR / "output")), name="media")

@app.get("/api/pipeline/status")
def get_status():
    """Return the current state of the supervisor and agents."""
    from supervisor import get_supervisor_state
    return get_supervisor_state()

@app.post("/api/pipeline/start")
def start_pipeline(background_tasks: BackgroundTasks):
    """Trigger the Team Leader to start the pipeline in the background."""
    if supervisor_state.is_running:
        return {"status": "error", "message": "Pipeline is already running."}
    
    # Run the Team Leader in a background thread so it doesn't block the API
    thread = threading.Thread(target=start_pipeline_run, kwargs={"max_videos": 1, "auto_upload": False})
    thread.start()
    
    return {"status": "started", "message": "Team Leader has started the pipeline."}

@app.get("/api/logs/stream")
async def stream_logs(request: Request):
    """Stream live logs from the supervisor using Server-Sent Events (SSE)."""
    async def log_generator():
        last_index = 0
        while True:
            if await request.is_disconnected():
                break
                
            # Yield any new logs
            current_logs = supervisor_state.get_logs()
            if len(current_logs) > last_index:
                for log_item in current_logs[last_index:]:
                    yield f"data: {json.dumps(log_item)}\n\n"
                last_index = len(current_logs)
                
            await asyncio.sleep(0.5)
            
    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.get("/api/content/queue")
def get_queue():
    """Return the items waiting for approval."""
    queue_file = config.DATA_DIR / "approval_queue.json"
    if queue_file.exists():
        return json.loads(queue_file.read_text(encoding="utf-8"))
    return []
