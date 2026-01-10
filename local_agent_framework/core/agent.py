"""
Agent Module - Core AI agent implementation

The Agent is the primary executor in the framework.
It uses LLMs to complete tasks, can use tools, and maintains memory.
"""

import json
import os
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field

# Try to import LLM providers
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

from .task import Task
from .memory import Memory, Message
from .tools import get_tool_schema, ToolKit


@dataclass 
class AgentConfig:
    """Configuration for an agent"""
    name: str = "Agent"
    role: str = ""
    goal: str = ""
    instructions: str = ""
    system_prompt: str = ""
    company_url: str = ""
    company_objective: str = ""
    max_iterations: int = 10
    debug: bool = False


class Agent:
    """
    AI Agent that can execute tasks using LLMs.
    
    Supports multiple LLM providers:
    - OpenAI: "openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-3.5-turbo"
    - Anthropic: "anthropic/claude-3-5-sonnet", "anthropic/claude-3-opus"
    - Ollama (local): "ollama/llama3.2", "ollama/mistral"
    
    Usage:
        agent = Agent(
            model="openai/gpt-4o",
            name="Assistant",
            role="General Purpose Assistant",
            goal="Help users with their tasks"
        )
        
        task = Task("What is 2 + 2?")
        result = agent.do(task)
        print(result)
    """
    
    def __init__(self,
                 model: str = "openai/gpt-4o",
                 name: str = "Agent",
                 role: str = "",
                 goal: str = "",
                 instructions: str = "",
                 system_prompt: str = "",
                 memory: Optional[Memory] = None,
                 agent_policy: Optional[Any] = None,
                 company_url: str = "",
                 company_objective: str = "",
                 debug: bool = False):
        """
        Initialize an agent.
        
        Args:
            model: LLM model in "provider/model" format
            name: Agent's name
            role: Agent's role description
            goal: Agent's primary goal
            instructions: Detailed instructions for the agent
            system_prompt: Custom system prompt (overrides auto-generated)
            memory: Memory instance for conversation history
            agent_policy: Safety policy to apply
            company_url: Company URL for context
            company_objective: Company mission/objective
            debug: Enable debug output
        """
        self.model = model
        self.config = AgentConfig(
            name=name,
            role=role,
            goal=goal,
            instructions=instructions,
            system_prompt=system_prompt,
            company_url=company_url,
            company_objective=company_objective,
            debug=debug
        )
        self.memory = memory
        self.agent_policy = agent_policy
        self._client = None
        self._provider, self._model_name = self._parse_model(model)
    
    def _parse_model(self, model: str) -> tuple:
        """Parse model string into provider and model name"""
        if "/" in model:
            provider, model_name = model.split("/", 1)
            return provider.lower(), model_name
        # Default to OpenAI if no provider specified
        return "openai", model
    
    def _get_client(self):
        """Get or create the LLM client"""
        if self._client is not None:
            return self._client
        
        if self._provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("OpenAI not installed. Run: pip install openai")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._client = OpenAI(api_key=api_key)
            
        elif self._provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise ImportError("Anthropic not installed. Run: pip install anthropic")
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self._client = anthropic.Anthropic(api_key=api_key)
            
        elif self._provider == "ollama":
            if not HAS_OLLAMA:
                raise ImportError("Ollama not installed. Run: pip install ollama")
            self._client = ollama
            
        else:
            raise ValueError(f"Unknown provider: {self._provider}")
        
        return self._client
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt from agent config"""
        if self.config.system_prompt:
            return self.config.system_prompt
        
        parts = [f"You are {self.config.name}."]
        
        if self.config.role:
            parts.append(f"Your role: {self.config.role}")
        if self.config.goal:
            parts.append(f"Your goal: {self.config.goal}")
        if self.config.company_url:
            parts.append(f"Company: {self.config.company_url}")
        if self.config.company_objective:
            parts.append(f"Company objective: {self.config.company_objective}")
        if self.config.instructions:
            parts.append(f"\nInstructions:\n{self.config.instructions}")
        
        return "\n".join(parts)
    
    def _build_messages(self, task: Task) -> List[Dict[str, str]]:
        """Build message list for LLM call"""
        messages = []
        
        # System message
        system_prompt = self._build_system_prompt()
        messages.append({"role": "system", "content": system_prompt})
        
        # Memory context
        if self.memory:
            memory_context = self.memory.get_context()
            if memory_context:
                messages.append({"role": "system", "content": f"Context:\n{memory_context}"})
            
            # Previous messages
            for msg in self.memory.get_messages_for_prompt():
                messages.append(msg)
        
        # Task as user message
        messages.append({"role": "user", "content": task.to_prompt()})
        
        return messages
    
    def _get_tool_schemas(self, task: Task) -> List[Dict[str, Any]]:
        """Get tool schemas for a task"""
        schemas = []
        for tool in task.tools:
            if isinstance(tool, type) and issubclass(tool, ToolKit):
                # It's a toolkit class
                toolkit = tool()
                schemas.extend(toolkit.get_tool_schemas())
            elif isinstance(tool, ToolKit):
                # It's a toolkit instance
                schemas.extend(tool.get_tool_schemas())
            elif hasattr(tool, "_is_tool"):
                # It's a single tool function
                schemas.append(get_tool_schema(tool))
            elif callable(tool):
                # It's a regular function - wrap it
                schemas.append({
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__ or "No description",
                        "parameters": {"type": "object", "properties": {}}
                    }
                })
        return schemas
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any], task: Task) -> Any:
        """Execute a tool by name"""
        for tool in task.tools:
            if isinstance(tool, type) and issubclass(tool, ToolKit):
                toolkit = tool()
                for t in toolkit.get_tools():
                    if t._tool_name == tool_name:
                        return t(**arguments)
            elif isinstance(tool, ToolKit):
                for t in tool.get_tools():
                    if t._tool_name == tool_name:
                        return t(**arguments)
            elif hasattr(tool, "_is_tool") and tool._tool_name == tool_name:
                return tool(**arguments)
            elif callable(tool) and tool.__name__ == tool_name:
                return tool(**arguments)
        
        raise ValueError(f"Tool not found: {tool_name}")
    
    def _call_openai(self, messages: List[Dict], tools: List[Dict], task: Task) -> str:
        """Call OpenAI API"""
        client = self._get_client()
        
        kwargs = {
            "model": self._model_name,
            "messages": messages,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        # Handle response format
        if task.response_format:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        # Handle tool calls
        if message.tool_calls:
            # Add assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            # Execute tools and add results
            for tool_call in message.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)
                    result = self._execute_tool(tool_call.function.name, args, task)
                    tool_result = str(result.result if hasattr(result, "result") else result)
                except Exception as e:
                    tool_result = f"Error: {e}"
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Get final response
            response = client.chat.completions.create(**kwargs)
            message = response.choices[0].message
        
        return message.content
    
    def _call_anthropic(self, messages: List[Dict], tools: List[Dict], task: Task) -> str:
        """Call Anthropic API"""
        client = self._get_client()
        
        # Convert messages to Anthropic format
        system_content = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_content += msg["content"] + "\n"
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        kwargs = {
            "model": self._model_name,
            "max_tokens": 4096,
            "messages": anthropic_messages,
        }
        
        if system_content:
            kwargs["system"] = system_content.strip()
        
        # Anthropic tool format is different - convert if needed
        if tools:
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })
            kwargs["tools"] = anthropic_tools
        
        response = client.messages.create(**kwargs)
        
        # Handle tool use
        result_text = ""
        for block in response.content:
            if block.type == "text":
                result_text += block.text
            elif block.type == "tool_use":
                # Execute tool
                try:
                    result = self._execute_tool(block.name, block.input, task)
                    tool_result = str(result.result if hasattr(result, "result") else result)
                except Exception as e:
                    tool_result = f"Error: {e}"
                
                # Continue conversation with tool result
                anthropic_messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    }]
                })
                
                # Get final response
                kwargs["messages"] = anthropic_messages
                response = client.messages.create(**kwargs)
                for b in response.content:
                    if b.type == "text":
                        result_text += b.text
        
        return result_text
    
    def _call_ollama(self, messages: List[Dict], tools: List[Dict], task: Task) -> str:
        """Call Ollama API (local)"""
        client = self._get_client()
        
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        response = client.chat(
            model=self._model_name,
            messages=ollama_messages
        )
        
        return response.message.content
    
    def do(self, task: Task) -> Any:
        """
        Execute a task and return the result.
        
        Args:
            task: Task to execute
        
        Returns:
            Task result (string or structured output if response_format specified)
        """
        # Build messages
        messages = self._build_messages(task)
        
        # Get tool schemas
        tools = self._get_tool_schemas(task) if task.tools else []
        
        if self.config.debug:
            print(f"[DEBUG] Agent: {self.config.name}")
            print(f"[DEBUG] Model: {self.model}")
            print(f"[DEBUG] Task: {task.description[:100]}...")
            print(f"[DEBUG] Tools: {len(tools)}")
        
        # Call appropriate provider
        if self._provider == "openai":
            result = self._call_openai(messages, tools, task)
        elif self._provider == "anthropic":
            result = self._call_anthropic(messages, tools, task)
        elif self._provider == "ollama":
            result = self._call_ollama(messages, tools, task)
        else:
            raise ValueError(f"Unknown provider: {self._provider}")
        
        # Apply policy if set
        if self.agent_policy:
            result = self._apply_policy(result)
        
        # Handle structured output
        if task.response_format:
            try:
                data = json.loads(result)
                result = task.response_format(**data)
            except (json.JSONDecodeError, Exception) as e:
                if self.config.debug:
                    print(f"[DEBUG] Failed to parse structured output: {e}")
        
        # Store response
        task.set_response(result)
        
        # Update memory
        if self.memory:
            self.memory.add_message("user", task.description)
            self.memory.add_message("assistant", str(result))
        
        return result
    
    def print_do(self, task: Task) -> Any:
        """Execute a task and print the result"""
        result = self.do(task)
        print(f"\n{'='*50}")
        print(f"Agent: {self.config.name}")
        print(f"Task: {task.description}")
        print(f"{'='*50}")
        print(f"Result:\n{result}")
        print(f"{'='*50}\n")
        return result
    
    def _apply_policy(self, text: str) -> str:
        """Apply safety policy to text (placeholder for full implementation)"""
        # In full implementation, this would check against policy rules
        return text
    
    async def do_async(self, task: Task) -> Any:
        """Async version of do() - placeholder for async implementation"""
        # For now, just call sync version
        # In production, use async LLM clients
        return self.do(task)
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.config.name}', model='{self.model}')"
