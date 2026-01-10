"""
Team Module - Multi-agent coordination

Teams allow multiple agents to work together on complex tasks.
Supports different coordination modes: sequential, coordinate, and route.
"""

from typing import Any, List, Literal, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .agent import Agent
from .task import Task


class TeamMode(str, Enum):
    """Available team coordination modes"""
    SEQUENTIAL = "sequential"  # Tasks flow from one agent to next
    COORDINATE = "coordinate"  # Leader agent coordinates others
    ROUTE = "route"           # Router selects best agent per task


@dataclass
class TeamResult:
    """Result from team execution"""
    final_result: Any
    task_results: List[Any]
    agents_used: List[str]


class Team:
    """
    A team of agents that work together on tasks.
    
    Modes:
    - sequential: Tasks flow from one agent to the next, each building on previous work
    - coordinate: A leader agent coordinates specialized agents
    - route: An intelligent router selects the best agent for each task
    
    Usage:
        researcher = Agent(model="openai/gpt-4o", name="Researcher", role="Research Specialist")
        writer = Agent(model="openai/gpt-4o", name="Writer", role="Content Writer")
        
        team = Team(agents=[researcher, writer], mode="sequential")
        
        tasks = [
            Task("Research quantum computing"),
            Task("Write a blog post about quantum computing")
        ]
        
        result = team.do(tasks)
    """
    
    def __init__(self,
                 agents: List[Agent],
                 mode: Union[TeamMode, str] = TeamMode.SEQUENTIAL,
                 model: Optional[str] = None,
                 verbose: bool = False):
        """
        Initialize a team.
        
        Args:
            agents: List of agents in the team
            mode: Coordination mode (sequential, coordinate, route)
            model: LLM model for leader/router (required for coordinate/route modes)
            verbose: Enable verbose output
        """
        if not agents:
            raise ValueError("Team must have at least one agent")
        
        self.agents = agents
        self.mode = TeamMode(mode) if isinstance(mode, str) else mode
        self.model = model
        self.verbose = verbose
        
        # Validate requirements
        if self.mode in [TeamMode.COORDINATE, TeamMode.ROUTE] and not model:
            raise ValueError(f"{self.mode.value} mode requires a model for the leader/router")
    
    def _select_agent_for_task(self, task: Task, available_agents: List[Agent]) -> Agent:
        """Select the best agent for a task based on role/goal matching"""
        # If task has assigned agent, use it
        if task.agent:
            return task.agent
        
        # Simple heuristic: match task keywords to agent roles/goals
        task_lower = task.description.lower()
        
        best_agent = available_agents[0]
        best_score = 0
        
        for agent in available_agents:
            score = 0
            role_words = agent.config.role.lower().split()
            goal_words = agent.config.goal.lower().split()
            
            for word in role_words + goal_words:
                if len(word) > 3 and word in task_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    def _run_sequential(self, tasks: List[Task]) -> TeamResult:
        """
        Run tasks sequentially, each agent building on previous work.
        
        Each task is assigned to the best matching agent.
        Later tasks receive context from earlier task results.
        """
        results = []
        agents_used = []
        
        for i, task in enumerate(tasks):
            # Select agent
            agent = self._select_agent_for_task(task, self.agents)
            agents_used.append(agent.config.name)
            
            if self.verbose:
                print(f"[Team] Task {i+1}/{len(tasks)}: {agent.config.name}")
            
            # Add previous results as context
            if i > 0 and results:
                prev_task = tasks[i-1]
                if prev_task not in task.context:
                    task.context.append(prev_task)
            
            # Execute
            result = agent.do(task)
            results.append(result)
        
        return TeamResult(
            final_result=results[-1] if results else None,
            task_results=results,
            agents_used=agents_used
        )
    
    def _run_coordinate(self, tasks: List[Task]) -> TeamResult:
        """
        Run with a leader agent coordinating others.
        
        The leader agent decides which specialist to use for each task
        and synthesizes the final result.
        """
        # Create leader agent
        agent_descriptions = "\n".join([
            f"- {a.config.name}: {a.config.role} - {a.config.goal}"
            for a in self.agents
        ])
        
        leader = Agent(
            model=self.model,
            name="Team Leader",
            role="Team Coordinator",
            goal="Coordinate team members to complete tasks effectively",
            instructions=f"""You are coordinating a team of specialists:
{agent_descriptions}

For each task, decide which specialist should handle it.
After all tasks are complete, synthesize the final result."""
        )
        
        results = []
        agents_used = ["Team Leader"]
        
        for i, task in enumerate(tasks):
            # Ask leader which agent should handle this
            if self.verbose:
                print(f"[Team] Leader coordinating task {i+1}/{len(tasks)}")
            
            # Simple approach: leader selects agent and task is executed
            agent = self._select_agent_for_task(task, self.agents)
            agents_used.append(agent.config.name)
            
            # Add context from previous tasks
            if i > 0:
                task.context.extend([t for t in tasks[:i] if t.response])
            
            result = agent.do(task)
            results.append(result)
        
        # Leader synthesizes final result
        synthesis_task = Task(
            description=f"Synthesize these results into a coherent final answer:\n" +
                       "\n".join([f"- {r}" for r in results])
        )
        final_result = leader.do(synthesis_task)
        
        return TeamResult(
            final_result=final_result,
            task_results=results,
            agents_used=agents_used
        )
    
    def _run_route(self, tasks: Union[Task, List[Task]]) -> TeamResult:
        """
        Route each task to the single best agent.
        
        An intelligent router analyzes each task and selects
        the most appropriate specialist.
        """
        # Ensure tasks is a list
        if isinstance(tasks, Task):
            tasks = [tasks]
        
        results = []
        agents_used = ["Router"]
        
        for i, task in enumerate(tasks):
            # Select best agent for this specific task
            agent = self._select_agent_for_task(task, self.agents)
            agents_used.append(agent.config.name)
            
            if self.verbose:
                print(f"[Team] Routed task {i+1} to {agent.config.name}")
            
            result = agent.do(task)
            results.append(result)
        
        return TeamResult(
            final_result=results[-1] if results else None,
            task_results=results,
            agents_used=agents_used
        )
    
    def do(self, tasks: Union[Task, List[Task]]) -> Any:
        """
        Execute tasks with the team.
        
        Args:
            tasks: Single task or list of tasks
        
        Returns:
            Final result from the team
        """
        # Normalize to list
        if isinstance(tasks, Task):
            tasks = [tasks]
        
        if not tasks:
            raise ValueError("No tasks provided")
        
        # Run based on mode
        if self.mode == TeamMode.SEQUENTIAL:
            result = self._run_sequential(tasks)
        elif self.mode == TeamMode.COORDINATE:
            result = self._run_coordinate(tasks)
        elif self.mode == TeamMode.ROUTE:
            result = self._run_route(tasks)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        
        if self.verbose:
            print(f"[Team] Completed. Agents used: {', '.join(result.agents_used)}")
        
        return result.final_result
    
    def print_do(self, tasks: Union[Task, List[Task]]) -> Any:
        """Execute tasks and print the result"""
        result = self.do(tasks)
        print(f"\n{'='*50}")
        print(f"Team Mode: {self.mode.value}")
        print(f"Agents: {', '.join(a.config.name for a in self.agents)}")
        print(f"{'='*50}")
        print(f"Result:\n{result}")
        print(f"{'='*50}\n")
        return result
    
    def __repr__(self) -> str:
        agent_names = ", ".join(a.config.name for a in self.agents)
        return f"Team(mode={self.mode.value}, agents=[{agent_names}])"
