"""Memory Service - Manages sessions and conversation history"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime
import sys
import os
import uuid

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import SessionCreate, SessionResponse, HealthResponse
from shared.database import Base, get_db, engine, init_db

# Database Models
class SessionDB(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, unique=True, nullable=False)
    storage_type = Column(String, default="memory")
    created_at = Column(DateTime, default=datetime.utcnow)

class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
init_db()

# FastAPI App
app = FastAPI(title="Memory Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        service="memory-service",
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/sessions", response_model=SessionResponse)
async def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    """Create a new session"""
    # Check if session already exists
    existing = db.query(SessionDB).filter(SessionDB.session_id == session.session_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Session already exists")

    db_session = SessionDB(
        session_id=session.session_id,
        storage_type=session.storage_type
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return SessionResponse(
        session_id=db_session.session_id,
        storage_type=db_session.storage_type,
        created_at=db_session.created_at.isoformat()
    )

@app.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(db: Session = Depends(get_db)):
    """List all sessions"""
    sessions = db.query(SessionDB).all()
    return [
        SessionResponse(
            session_id=session.session_id,
            storage_type=session.storage_type,
            created_at=session.created_at.isoformat()
        )
        for session in sessions
    ]

@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session by ID"""
    session = db.query(SessionDB).filter(SessionDB.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.session_id,
        storage_type=session.storage_type,
        created_at=session.created_at.isoformat()
    )

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a session"""
    session = db.query(SessionDB).filter(SessionDB.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete associated messages
    db.query(MessageDB).filter(MessageDB.session_id == session_id).delete()

    # Delete session
    db.delete(session)
    db.commit()

    return {"message": "Session deleted", "session_id": session_id}

@app.post("/sessions/{session_id}/messages")
async def add_message(session_id: str, role: str, content: str, db: Session = Depends(get_db)):
    """Add a message to session"""
    # Verify session exists
    session = db.query(SessionDB).filter(SessionDB.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = MessageDB(
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(message)
    db.commit()

    return {"message": "Message added", "session_id": session_id}

@app.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages for a session"""
    messages = db.query(MessageDB).filter(MessageDB.session_id == session_id).order_by(MessageDB.created_at).all()
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
