"""Agent Service - Manages agent CRUD operations"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime
import sys
import os
import uuid

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import AgentCreate, AgentResponse, HealthResponse
from shared.database import Base, get_db, engine, init_db

# Database Model
class AgentDB(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, default="default")
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    role = Column(String, default="")
    goal = Column(String, default="")
    instructions = Column(String, default="")
    status = Column(String, default="active")
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
init_db()

# FastAPI App
app = FastAPI(title="Agent Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store (for demo - replace with DB in production)
agents_store = {}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        service="agent-service",
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent"""
    try:
        db_agent = AgentDB(
            user_id=agent.user_id,
            name=agent.name,
            model=agent.model,
            role=agent.role,
            goal=agent.goal,
            instructions=agent.instructions,
            status="active",
            config={"enable_memory": agent.enable_memory}
        )
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)

        return AgentResponse(
            id=db_agent.id,
            user_id=db_agent.user_id,
            name=db_agent.name,
            model=db_agent.model,
            role=db_agent.role,
            goal=db_agent.goal,
            instructions=db_agent.instructions,
            status=db_agent.status,
            created_at=db_agent.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents", response_model=list[AgentResponse])
async def list_agents(db: Session = Depends(get_db)):
    """List all agents"""
    agents = db.query(AgentDB).all()
    return [
        AgentResponse(
            id=agent.id,
            user_id=agent.user_id,
            name=agent.name,
            model=agent.model,
            role=agent.role,
            goal=agent.goal,
            instructions=agent.instructions,
            status=agent.status,
            created_at=agent.created_at.isoformat()
        )
        for agent in agents
    ]

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent by ID"""
    agent = db.query(AgentDB).filter(AgentDB.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse(
        id=agent.id,
        user_id=agent.user_id,
        name=agent.name,
        model=agent.model,
        role=agent.role,
        goal=agent.goal,
        instructions=agent.instructions,
        status=agent.status,
        created_at=agent.created_at.isoformat()
    )

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent"""
    agent = db.query(AgentDB).filter(AgentDB.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted", "agent_id": agent_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
