"""Task Service - Executes agent tasks with LLM providers"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Float, Text
from datetime import datetime
import sys
import os
import uuid
import time
import httpx

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import TaskCreate, TaskResponse, HealthResponse
from shared.database import Base, get_db, engine, init_db

# Import LLM provider
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from local_agent_framework import Agent, Task as FrameworkTask

# Database Model
class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    result = Column(Text)
    status = Column(String, default="pending")
    execution_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

# Create tables
init_db()

# FastAPI App
app = FastAPI(title="Task Executor Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8001")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        service="task-service",
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/tasks", response_model=TaskResponse)
async def execute_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Execute a task"""
    start_time = time.time()

    try:
        # Get agent details from agent service
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AGENT_SERVICE_URL}/agents/{task.agent_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Agent not found")
            agent_data = response.json()

        # Create task in database
        db_task = TaskDB(
            agent_id=task.agent_id,
            description=task.description,
            status="executing"
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        # Execute task using framework
        agent = Agent(
            model=agent_data["model"],
            name=agent_data["name"]
        )
        framework_task = FrameworkTask(task.description)
        result = agent.do(framework_task)

        # Update task with result
        execution_time = (time.time() - start_time) * 1000
        db_task.result = result
        db_task.status = "completed"
        db_task.execution_time_ms = execution_time
        db_task.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_task)

        return TaskResponse(
            id=db_task.id,
            agent_id=db_task.agent_id,
            description=db_task.description,
            result=db_task.result,
            status=db_task.status,
            execution_time_ms=db_task.execution_time_ms,
            created_at=db_task.created_at.isoformat(),
            completed_at=db_task.completed_at.isoformat() if db_task.completed_at else None
        )

    except Exception as e:
        # Update task with error
        if 'db_task' in locals():
            db_task.status = "failed"
            db_task.result = f"Error: {str(e)}"
            db_task.completed_at = datetime.utcnow()
            db.commit()

        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(db: Session = Depends(get_db)):
    """List all tasks"""
    tasks = db.query(TaskDB).all()
    return [
        TaskResponse(
            id=task.id,
            agent_id=task.agent_id,
            description=task.description,
            result=task.result,
            status=task.status,
            execution_time_ms=task.execution_time_ms,
            created_at=task.created_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        )
        for task in tasks
    ]

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get task by ID"""
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        id=task.id,
        agent_id=task.agent_id,
        description=task.description,
        result=task.result,
        status=task.status,
        execution_time_ms=task.execution_time_ms,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )

@app.get("/agents/{agent_id}/tasks", response_model=list[TaskResponse])
async def get_agent_tasks(agent_id: str, db: Session = Depends(get_db)):
    """Get all tasks for an agent"""
    tasks = db.query(TaskDB).filter(TaskDB.agent_id == agent_id).all()
    return [
        TaskResponse(
            id=task.id,
            agent_id=task.agent_id,
            description=task.description,
            result=task.result,
            status=task.status,
            execution_time_ms=task.execution_time_ms,
            created_at=task.created_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        )
        for task in tasks
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
