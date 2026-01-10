"""
Local Agent Framework - A Simple AI Agent Framework

A lightweight, local-first alternative to Upsonic for building AI agents.
Supports OpenAI, Anthropic, and Ollama (local) LLMs.

Basic Usage:
    from local_agent_framework import Agent, Task
    
    agent = Agent(model="openai/gpt-4o", name="Assistant")
    task = Task("What is 2 + 2?")
    result = agent.do(task)
    print(result)

With Memory:
    from local_agent_framework import Agent, Task, Memory, InMemoryStorage
    
    memory = Memory(storage=InMemoryStorage(), session_id="session_001")
    agent = Agent(model="openai/gpt-4o", memory=memory)
    
    agent.do(Task("My name is John"))
    agent.do(Task("What is my name?"))  # Remembers: John

With Tools:
    from local_agent_framework import Agent, Task, tool
    
    @tool
    def get_weather(city: str) -> str:
        '''Get weather for a city'''
        return f"Sunny in {city}"
    
    agent = Agent(model="openai/gpt-4o")
    task = Task("What's the weather in Paris?", tools=[get_weather])
    result = agent.do(task)

With Teams:
    from local_agent_framework import Agent, Task, Team
    
    researcher = Agent(model="openai/gpt-4o", name="Researcher", role="Research")
    writer = Agent(model="openai/gpt-4o", name="Writer", role="Writing")
    
    team = Team(agents=[researcher, writer], mode="sequential")
    tasks = [
        Task("Research AI trends"),
        Task("Write a blog post about AI")
    ]
    result = team.do(tasks)

With Safety Policies:
    from local_agent_framework import Agent, Task
    from local_agent_framework.safety import PIIAnonymizePolicy
    
    agent = Agent(model="openai/gpt-4o", agent_policy=PIIAnonymizePolicy)
    result = agent.do(Task("My email is test@example.com"))
    # Output will have email anonymized
"""

__version__ = "0.1.0"
__author__ = "Local Agent Framework"

# Core components
from .core.agent import Agent
from .core.task import Task
from .core.team import Team, TeamMode
from .core.memory import Memory, InMemoryStorage, SqliteStorage, Message
from .core.tools import tool, ToolKit, ToolResult, get_tool_schema, web_search, calculator

# Safety components  
from .core.safety import (
    SafetyEngine,
    Policy,
    Rule,
    Action,
    PIIRule,
    RegexRule,
    BlockAction,
    AnonymizeAction,
    ReplaceAction,
    RaiseAction,
    PIIBlockPolicy,
    PIIAnonymizePolicy,
    PIIReplacePolicy,
    PIIRaiseExceptionPolicy,
    PolicyViolation,
    DisallowedOperation
)

__all__ = [
    # Core
    "Agent",
    "Task", 
    "Team",
    "TeamMode",
    "Memory",
    "InMemoryStorage",
    "SqliteStorage",
    "Message",
    
    # Tools
    "tool",
    "ToolKit",
    "ToolResult",
    "get_tool_schema",
    "web_search",
    "calculator",
    
    # Safety
    "SafetyEngine",
    "Policy",
    "Rule",
    "Action",
    "PIIRule",
    "RegexRule",
    "BlockAction",
    "AnonymizeAction",
    "ReplaceAction", 
    "RaiseAction",
    "PIIBlockPolicy",
    "PIIAnonymizePolicy",
    "PIIReplacePolicy",
    "PIIRaiseExceptionPolicy",
    "PolicyViolation",
    "DisallowedOperation",
]
