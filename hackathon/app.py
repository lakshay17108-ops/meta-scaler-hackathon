from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from smartlogistics import LogisticsEnv, TASKS, TASK_MAP
from smartlogistics.models import Action

app = FastAPI(title="Smart Logistics OpenEnv")

app.state.env = LogisticsEnv(TASKS[0].scenario)
app.state.current_task = TASKS[0].id


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "Smart Logistics OpenEnv",
        "current_task": app.state.current_task,
        "tasks": [task.id for task in TASKS],
    }


@app.post("/reset")
def reset(task_id: Optional[str] = Query(None, description="Task id to reset")):
    if task_id is None:
        task_id = app.state.current_task
    if task_id not in TASK_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown task_id {task_id}")
    app.state.current_task = task_id
    app.state.env = LogisticsEnv(TASK_MAP[task_id].scenario)
    observation = app.state.env.reset()
    return {"observation": observation.model_dump(), "done": app.state.env.done}


@app.post("/step")
def step(action: Action):
    if not hasattr(app.state, "env") or app.state.env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized. Call /reset first.")
    state = app.state.env.step(action)
    return state.model_dump()


@app.get("/state")
def state():
    if not hasattr(app.state, "env") or app.state.env is None:
        raise HTTPException(status_code=500, detail="Environment not initialized. Call /reset first.")
    return app.state.env.state().model_dump()
