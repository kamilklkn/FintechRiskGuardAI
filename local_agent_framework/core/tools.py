"""
Tools Module - Create custom tools for agents

Provides decorators and base classes for creating tools that agents can use.
"""

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, get_type_hints
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None


def tool(func: Callable = None, *, 
         name: Optional[str] = None,
         description: Optional[str] = None,
         require_confirmation: bool = False) -> Callable:
    """
    Decorator to convert a function into an agent tool.
    
    Usage:
        @tool
        def my_tool(param: str) -> str:
            '''Tool description here'''
            return f"Result: {param}"
        
        @tool(name="custom_name", require_confirmation=True)
        def dangerous_tool(x: int) -> int:
            '''Does something dangerous'''
            return x * 2
    
    Args:
        func: The function to wrap
        name: Custom tool name (defaults to function name)
        description: Custom description (defaults to docstring)
        require_confirmation: If True, agent should confirm before running
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs) -> ToolResult:
            try:
                result = f(*args, **kwargs)
                return ToolResult(success=True, result=result)
            except Exception as e:
                return ToolResult(success=False, result=None, error=str(e))
        
        # Store tool metadata
        wrapper._is_tool = True
        wrapper._tool_name = name or f.__name__
        wrapper._tool_description = description or (f.__doc__ or "No description")
        wrapper._require_confirmation = require_confirmation
        wrapper._original_func = f
        
        # Extract parameter info from type hints
        try:
            hints = get_type_hints(f)
            sig = inspect.signature(f)
            wrapper._parameters = {
                name: {
                    "type": hints.get(name, Any).__name__ if hasattr(hints.get(name, Any), "__name__") else str(hints.get(name, Any)),
                    "required": param.default == inspect.Parameter.empty,
                    "default": None if param.default == inspect.Parameter.empty else param.default
                }
                for name, param in sig.parameters.items()
            }
        except Exception:
            wrapper._parameters = {}
        
        return wrapper
    
    # Handle both @tool and @tool() syntax
    if func is None:
        return decorator
    return decorator(func)


class ToolKit:
    """
    Base class for creating tool collections.
    
    Usage:
        class MyTools(ToolKit):
            @tool
            def search(self, query: str) -> str:
                '''Search for information'''
                return f"Results for: {query}"
            
            @tool  
            def calculate(self, expression: str) -> float:
                '''Evaluate math expression'''
                return eval(expression)
    """
    
    def get_tools(self) -> List[Callable]:
        """Get all tool methods from this toolkit"""
        tools = []
        for name in dir(self):
            if not name.startswith("_"):
                attr = getattr(self, name)
                if callable(attr) and hasattr(attr, "_is_tool"):
                    tools.append(attr)
        return tools
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible tool schemas for all tools"""
        schemas = []
        for tool_func in self.get_tools():
            schema = {
                "type": "function",
                "function": {
                    "name": tool_func._tool_name,
                    "description": tool_func._tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            for param_name, param_info in tool_func._parameters.items():
                if param_name == "self":
                    continue
                schema["function"]["parameters"]["properties"][param_name] = {
                    "type": _python_type_to_json(param_info["type"]),
                    "description": f"Parameter: {param_name}"
                }
                if param_info["required"]:
                    schema["function"]["parameters"]["required"].append(param_name)
            
            schemas.append(schema)
        return schemas


def get_tool_schema(func: Callable) -> Dict[str, Any]:
    """Get OpenAI-compatible schema for a single tool function"""
    if not hasattr(func, "_is_tool"):
        raise ValueError(f"{func.__name__} is not a tool. Use @tool decorator.")
    
    schema = {
        "type": "function",
        "function": {
            "name": func._tool_name,
            "description": func._tool_description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
    
    for param_name, param_info in func._parameters.items():
        schema["function"]["parameters"]["properties"][param_name] = {
            "type": _python_type_to_json(param_info["type"]),
            "description": f"Parameter: {param_name}"
        }
        if param_info["required"]:
            schema["function"]["parameters"]["required"].append(param_name)
    
    return schema


def _python_type_to_json(type_name: str) -> str:
    """Convert Python type names to JSON schema types"""
    mapping = {
        "str": "string",
        "int": "integer", 
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "List": "array",
        "dict": "object",
        "Dict": "object",
        "None": "null",
        "NoneType": "null",
    }
    return mapping.get(type_name, "string")


# Built-in common tools
@tool
def web_search(query: str) -> str:
    """
    Search the web for information (placeholder - implement with actual API).
    
    Args:
        query: Search query string
    
    Returns:
        Search results as text
    """
    # In real implementation, use requests to search API
    return f"[Web search results for: {query}] - Implement with actual search API"


@tool
def calculator(expression: str) -> float:
    """
    Safely evaluate a mathematical expression.
    
    Args:
        expression: Math expression like "2 + 2" or "sqrt(16)"
    
    Returns:
        Calculation result
    """
    import ast
    import operator
    import math
    
    # Safe operators
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }
    
    # Safe functions
    safe_funcs = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
    }
    
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return ops[type(node.op)](eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](eval_node(node.operand))
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name in safe_funcs:
                args = [eval_node(arg) for arg in node.args]
                return safe_funcs[func_name](*args)
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")
    
    tree = ast.parse(expression, mode="eval")
    return eval_node(tree.body)
