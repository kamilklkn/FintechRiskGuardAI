#!/usr/bin/env python3
"""
Local Agent Framework - Example Usage
Set your API key: export OPENAI_API_KEY=sk-...
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from local_agent_framework import (
    Agent, Task, Team, Memory, InMemoryStorage,
    tool, ToolKit, PIIAnonymizePolicy
)

# Example 1: Basic Agent
def basic_agent():
    agent = Agent(model="ollama/llama3.2", name="Assistant")
    agent.print_do(Task("What are the three laws of robotics?"))

# Example 2: Agent with Memory
def agent_with_memory():
    memory = Memory(storage=InMemoryStorage(), session_id="demo")
    agent = Agent(model="ollama/llama3.2", memory=memory)
    
    agent.print_do(Task("My name is Alice"))
    agent.print_do(Task("What's my name?"))  # Remembers!

# Example 3: Custom Tools
def custom_tools():
    @tool
    def get_weather(city: str) -> str:
        """Get weather for a city"""
        return f"Sunny, 25°C in {city}"
    
    @tool
    def calculate(expression: str) -> float:
        """Evaluate math expression"""
        return eval(expression)
    
    agent = Agent(model="ollama/llama3.2")
    task = Task(
        "Weather in Tokyo? And what's 25 * 4?",
        tools=[get_weather, calculate]
    )
    agent.print_do(task)

# Example 4: Multi-Agent Team
def team_example():
    researcher = Agent(model="ollama/llama3.2", name="Researcher", role="Research")
    writer = Agent(model="ollama/llama3.2", name="Writer", role="Writing")
    
    team = Team(agents=[researcher, writer], mode="sequential", verbose=True)
    
    tasks = [
        Task("Research 3 facts about honey bees"),
        Task("Write a paragraph about bees for children")
    ]
    team.print_do(tasks)

# Example 5: Safety Engine
def safety_example():
    agent = Agent(model="ollama/llama3.2", agent_policy=PIIAnonymizePolicy)
    agent.print_do(Task("My email is test@example.com, what is it?"))

if __name__ == "__main__":
    print("Choose example to run:")
    print("1. Basic Agent")
    print("2. Agent with Memory")
    print("3. Custom Tools")
    print("4. Multi-Agent Team")
    print("5. Safety Engine")
    
    choice = input("\nEnter number (1-5): ").strip()
    
    examples = {
        "1": basic_agent,
        "2": agent_with_memory,
        "3": custom_tools,
        "4": team_example,
        "5": safety_example
    }
    
    if choice in examples:
        examples[choice]()
    else:
        print("Running all examples...")
        for fn in examples.values():
            try:
                fn()
            except Exception as e:
                print(f"Error: {e}")
