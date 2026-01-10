"""
Task Module - Defines units of work for agents

Task is the fundamental unit of work in the agent framework.
Each task has a description, optional tools, context, and response format.
"""

from typing import Any, List, Optional, Type
from dataclasses import dataclass, field
from pydantic import BaseModel


@dataclass
class Task:
    """
    Represents a unit of work for an agent to complete.
    
    Attributes:
        description: What the agent should do
        tools: List of tools available for this task
        context: Additional context (other tasks, knowledge bases)
        response_format: Pydantic model for structured output
        response: The result after task completion
        agent: Assigned agent (for team scenarios)
    """
    description: str
    tools: List[Any] = field(default_factory=list)
    context: List[Any] = field(default_factory=list)
    response_format: Optional[Type[BaseModel]] = None
    response: Optional[Any] = None
    agent: Optional[Any] = None
    
    def __post_init__(self):
        """Validate task configuration"""
        if not self.description or not self.description.strip():
            raise ValueError("Task description cannot be empty")
    
    def set_response(self, response: Any) -> None:
        """Store the task response"""
        self.response = response
    
    def get_context_text(self) -> str:
        """Get context as text for prompt building"""
        context_parts = []
        for ctx in self.context:
            if isinstance(ctx, Task) and ctx.response:
                context_parts.append(f"Previous task result: {ctx.response}")
            elif hasattr(ctx, "query"):
                # Knowledge base context
                context_parts.append(f"Knowledge context: {ctx}")
            else:
                context_parts.append(str(ctx))
        return "\n".join(context_parts)
    
    def to_prompt(self) -> str:
        """Convert task to a prompt string"""
        prompt_parts = [f"Task: {self.description}"]
        
        context_text = self.get_context_text()
        if context_text:
            prompt_parts.insert(0, f"Context:\n{context_text}\n")
        
        if self.tools:
            tool_names = [t.__name__ if hasattr(t, "__name__") else str(t) for t in self.tools]
            prompt_parts.append(f"\nAvailable tools: {', '.join(tool_names)}")
        
        return "\n".join(prompt_parts)
    
    def __repr__(self) -> str:
        return f"Task(description='{self.description[:50]}...', tools={len(self.tools)})"
