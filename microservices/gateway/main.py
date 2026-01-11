"""API Gateway - Routes requests to appropriate microservices"""
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import os
from datetime import datetime
from typing import List

app = FastAPI(title="API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
AGENT_SERVICE = os.getenv("AGENT_SERVICE_URL", "http://localhost:8001")
TASK_SERVICE = os.getenv("TASK_SERVICE_URL", "http://localhost:8002")
MEMORY_SERVICE = os.getenv("MEMORY_SERVICE_URL", "http://localhost:8003")
RISK_SERVICE = os.getenv("RISK_SERVICE_URL", "http://localhost:8004")
EMAIL_SERVICE = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8005")

# Mount static files for admin panel
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def root():
    """Root endpoint - serve admin panel"""
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "API Gateway", "version": "1.0.0"}

@app.get("/admin")
async def admin():
    """Admin panel"""
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Admin panel not found"}

@app.get("/health")
async def health():
    """Gateway health check"""
    services_health = {}

    # Check all services
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in [
            ("agent", AGENT_SERVICE),
            ("task", TASK_SERVICE),
            ("memory", MEMORY_SERVICE),
            ("risk", RISK_SERVICE),
            ("email", EMAIL_SERVICE),
        ]:
            try:
                response = await client.get(f"{service_url}/health")
                services_health[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url
                }
            except:
                services_health[service_name] = {
                    "status": "unreachable",
                    "url": service_url
                }

    all_healthy = all(s["status"] == "healthy" for s in services_health.values())

    return {
        "service": "gateway",
        "status": "healthy" if all_healthy else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_health
    }

# ============ AGENT SERVICE ROUTES ============

@app.post("/api/v1/agents")
@app.post("/agents")
async def create_agent(request: Request):
    """Proxy to agent service"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AGENT_SERVICE}/agents", json=body)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/v1/agents")
@app.get("/agents")
async def list_agents():
    """Proxy to agent service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AGENT_SERVICE}/agents")
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/v1/agents/{agent_id}")
@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Proxy to agent service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AGENT_SERVICE}/agents/{agent_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.delete("/api/v1/agents/{agent_id}")
@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Proxy to agent service"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{AGENT_SERVICE}/agents/{agent_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)

# ============ TASK SERVICE ROUTES ============

@app.post("/api/v1/tasks")
@app.post("/tasks")
async def execute_task(request: Request):
    """Proxy to task service"""
    body = await request.json()
    async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for task execution
        response = await client.post(f"{TASK_SERVICE}/tasks", json=body)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/v1/tasks")
@app.get("/tasks")
async def list_tasks():
    """Proxy to task service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TASK_SERVICE}/tasks")
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/v1/tasks/{task_id}")
@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Proxy to task service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TASK_SERVICE}/tasks/{task_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/v1/agents/{agent_id}/tasks")
@app.get("/agents/{agent_id}/tasks")
async def get_agent_tasks(agent_id: str):
    """Proxy to task service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TASK_SERVICE}/agents/{agent_id}/tasks")
        return JSONResponse(content=response.json(), status_code=response.status_code)

# ============ QUICK EXECUTE ============

@app.post("/api/v1/quick")
@app.post("/quick")
async def quick_execute(request: Request):
    """Quick execute - create temp agent and execute task"""
    body = await request.json()

    try:
        # Create temporary agent
        async with httpx.AsyncClient() as client:
            agent_response = await client.post(f"{AGENT_SERVICE}/agents", json={
                "name": "QuickAgent",
                "model": body.get("model", "ollama/llama3.2"),
                "user_id": "quick"
            })

            if agent_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to create agent")

            agent_data = agent_response.json()
            agent_id = agent_data["id"]

            # Execute task
            task_response = await client.post(f"{TASK_SERVICE}/tasks", json={
                "agent_id": agent_id,
                "description": body["description"]
            }, timeout=60.0)

            # Delete temporary agent
            await client.delete(f"{AGENT_SERVICE}/agents/{agent_id}")

            return JSONResponse(content=task_response.json(), status_code=task_response.status_code)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ SESSIONS (MEMORY SERVICE) ============

@app.post("/api/v1/sessions")
@app.post("/sessions")
async def create_session(request: Request):
    """Proxy to memory service"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MEMORY_SERVICE}/sessions", json=body)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/v1/sessions")
@app.get("/sessions")
async def list_sessions():
    """Proxy to memory service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MEMORY_SERVICE}/sessions")
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.delete("/api/v1/sessions/{session_id}")
@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Proxy to memory service"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{MEMORY_SERVICE}/sessions/{session_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)

# ============ RISK SCORING SERVICE ============

@app.post("/api/v1/risk-score")
@app.post("/risk-score")
async def create_risk_score(request: Request):
    """Proxy to risk service"""
    body = await request.json()
    async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for risk scoring
        response = await client.post(f"{RISK_SERVICE}/risk-score", json=body)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/v1/risk-score/{application_id}")
@app.get("/risk-score/{application_id}")
async def get_risk_score(application_id: str):
    """Proxy to risk service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RISK_SERVICE}/risk-score/{application_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/v1/risk-scores")
@app.get("/risk-scores")
async def list_risk_scores():
    """Proxy to risk service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RISK_SERVICE}/risk-scores")
        return JSONResponse(content=response.json(), status_code=response.status_code)

# ============ EMAIL SERVICE ============

@app.post("/api/v1/send-report")
@app.post("/send-report")
async def send_report(request: Request):
    """Proxy to email service"""
    body = await request.json()
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{EMAIL_SERVICE}/send-report", json=body)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/api/v1/send-test-email")
@app.post("/send-test-email")
async def send_test_email(request: Request):
    """Proxy to email service"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{EMAIL_SERVICE}/send-test-email", params={"email": body.get("email")})
        return JSONResponse(content=response.json(), status_code=response.status_code)

# ============ OCR DOCUMENT PROCESSING ============

@app.post("/api/v1/ocr-documents")
@app.post("/ocr-documents")
async def ocr_documents(files: List[UploadFile] = File(...)):
    """Process uploaded documents with OCR and extract merchant information"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Forward files to risk service for OCR processing
        files_data = []
        for file in files:
            content = await file.read()
            files_data.append(('files', (file.filename, content, file.content_type)))

        response = await client.post(
            f"{RISK_SERVICE}/ocr-extract",
            files=files_data
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
