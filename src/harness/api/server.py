"""REST API for the harness using FastAPI."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Cognitive Harness API", version="3.0.0")

_harness = None


def set_harness(harness):
    global _harness
    _harness = harness


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    if request.session_id:
        await _harness.resume_session(request.session_id)
    response = await _harness.chat(request.message)
    return ChatResponse(response=response, session_id=_harness._session.id)


@app.get("/sessions")
async def list_sessions():
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    return await _harness.list_sessions()


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    session = _harness._session_manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    await _harness.resume_session(session_id)
    return {"status": "resumed", "session_id": session_id}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    _harness._session_manager.delete_session(session_id)
    return {"status": "deleted"}


@app.get("/skills")
async def list_skills():
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    return await _harness.list_skills()


@app.get("/tools")
async def list_tools():
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    return _harness._tool_registry.get_all_tools()


@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, parameters: dict = {}):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    try:
        result = _harness._tool_registry.execute(tool_name, parameters)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
