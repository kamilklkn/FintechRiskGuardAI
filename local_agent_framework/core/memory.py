"""
Memory Module - Persistent storage for agent conversations

Provides memory systems for agents to remember past interactions,
user information, and conversation context.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Message:
    """A single message in a conversation"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            metadata=data.get("metadata", {})
        )


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def save_messages(self, session_id: str, messages: List[Message]) -> None:
        """Save messages for a session"""
        pass
    
    @abstractmethod
    def load_messages(self, session_id: str) -> List[Message]:
        """Load messages for a session"""
        pass
    
    @abstractmethod
    def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> None:
        """Save user profile data"""
        pass
    
    @abstractmethod
    def load_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Load user profile data"""
        pass
    
    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session"""
        pass


class InMemoryStorage(StorageBackend):
    """
    In-memory storage backend (data lost on restart).
    Good for testing and short-lived sessions.
    """
    
    def __init__(self):
        self._sessions: Dict[str, List[Message]] = {}
        self._profiles: Dict[str, Dict[str, Any]] = {}
    
    def save_messages(self, session_id: str, messages: List[Message]) -> None:
        self._sessions[session_id] = messages
    
    def load_messages(self, session_id: str) -> List[Message]:
        return self._sessions.get(session_id, [])
    
    def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> None:
        self._profiles[user_id] = profile
    
    def load_user_profile(self, user_id: str) -> Dict[str, Any]:
        return self._profiles.get(user_id, {})
    
    def clear_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]


class SqliteStorage(StorageBackend):
    """
    SQLite-based persistent storage.
    Good for local persistence across restarts.
    """
    
    def __init__(self, 
                 db_path: str = "./agent_memory.db",
                 sessions_table: str = "sessions",
                 profiles_table: str = "profiles"):
        self.db_path = Path(db_path)
        self.sessions_table = sessions_table
        self.profiles_table = profiles_table
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.sessions_table} (
                    session_id TEXT,
                    message_index INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    metadata TEXT,
                    PRIMARY KEY (session_id, message_index)
                )
            """)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.profiles_table} (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()
    
    def save_messages(self, session_id: str, messages: List[Message]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            # Clear existing messages for session
            conn.execute(
                f"DELETE FROM {self.sessions_table} WHERE session_id = ?",
                (session_id,)
            )
            # Insert new messages
            for idx, msg in enumerate(messages):
                conn.execute(
                    f"""INSERT INTO {self.sessions_table} 
                        (session_id, message_index, role, content, timestamp, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                    (session_id, idx, msg.role, msg.content, 
                     msg.timestamp.isoformat(), json.dumps(msg.metadata))
                )
            conn.commit()
    
    def load_messages(self, session_id: str) -> List[Message]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""SELECT role, content, timestamp, metadata 
                    FROM {self.sessions_table}
                    WHERE session_id = ?
                    ORDER BY message_index""",
                (session_id,)
            )
            messages = []
            for row in cursor:
                messages.append(Message(
                    role=row[0],
                    content=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    metadata=json.loads(row[3])
                ))
            return messages
    
    def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""INSERT OR REPLACE INTO {self.profiles_table}
                    (user_id, profile_data, updated_at)
                    VALUES (?, ?, ?)""",
                (user_id, json.dumps(profile), datetime.now().isoformat())
            )
            conn.commit()
    
    def load_user_profile(self, user_id: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT profile_data FROM {self.profiles_table} WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return json.loads(row[0]) if row else {}
    
    def clear_session(self, session_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"DELETE FROM {self.sessions_table} WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()


class Memory:
    """
    Memory system for agents with conversation history and user profiles.
    
    Features:
    - Full conversation memory (all messages)
    - Summary memory (compressed summaries)
    - User analysis (learns about user)
    
    Usage:
        memory = Memory(
            storage=InMemoryStorage(),  # or SqliteStorage()
            session_id="session_001",
            user_id="user_001",
            full_session_memory=True,
            summary_memory=True,
            user_analysis_memory=True
        )
        
        agent = Agent(model="...", memory=memory)
    """
    
    def __init__(self,
                 storage: StorageBackend,
                 session_id: str,
                 user_id: Optional[str] = None,
                 full_session_memory: bool = True,
                 summary_memory: bool = False,
                 user_analysis_memory: bool = False,
                 num_last_messages: int = 50,
                 model: Optional[str] = None):
        """
        Initialize memory system.
        
        Args:
            storage: Storage backend (InMemoryStorage or SqliteStorage)
            session_id: Unique identifier for this conversation session
            user_id: Optional user identifier for cross-session memory
            full_session_memory: Keep all conversation messages
            summary_memory: Generate conversation summaries
            user_analysis_memory: Learn and store user preferences
            num_last_messages: Max messages to keep in context
            model: LLM model for summary/analysis (required if those are enabled)
        """
        self.storage = storage
        self.session_id = session_id
        self.user_id = user_id
        self.full_session_memory = full_session_memory
        self.summary_memory = summary_memory
        self.user_analysis_memory = user_analysis_memory
        self.num_last_messages = num_last_messages
        self.model = model
        
        # Load existing messages
        self._messages = storage.load_messages(session_id)
        self._user_profile = storage.load_user_profile(user_id) if user_id else {}
        self._summary = ""
    
    def add_message(self, role: str, content: str, **metadata) -> None:
        """Add a message to the conversation history"""
        msg = Message(role=role, content=content, metadata=metadata)
        self._messages.append(msg)
        
        # Auto-save
        if self.full_session_memory:
            self.storage.save_messages(self.session_id, self._messages)
    
    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get conversation messages, optionally limited to recent ones"""
        n = limit or self.num_last_messages
        return self._messages[-n:] if n else self._messages
    
    def get_messages_for_prompt(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM prompt"""
        messages = self.get_messages()
        return [{"role": m.role, "content": m.content} for m in messages]
    
    def get_context(self) -> str:
        """Get full context including summary and user profile"""
        parts = []
        
        if self._summary:
            parts.append(f"Conversation Summary:\n{self._summary}")
        
        if self._user_profile:
            parts.append(f"User Profile:\n{json.dumps(self._user_profile, indent=2)}")
        
        return "\n\n".join(parts)
    
    def update_user_profile(self, updates: Dict[str, Any]) -> None:
        """Update user profile with new information"""
        self._user_profile.update(updates)
        if self.user_id:
            self.storage.save_user_profile(self.user_id, self._user_profile)
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile"""
        return self._user_profile.copy()
    
    def clear(self) -> None:
        """Clear conversation history"""
        self._messages = []
        self.storage.clear_session(self.session_id)
    
    def generate_summary(self, llm_client: Any = None) -> str:
        """
        Generate a summary of the conversation (requires LLM).
        
        This is a placeholder - in real implementation, 
        call the LLM to summarize the conversation.
        """
        if not self._messages:
            return ""
        
        # Placeholder - implement with actual LLM call
        message_count = len(self._messages)
        self._summary = f"[Conversation summary: {message_count} messages exchanged]"
        return self._summary
    
    def __len__(self) -> int:
        return len(self._messages)
    
    def __repr__(self) -> str:
        return f"Memory(session={self.session_id}, messages={len(self._messages)})"
