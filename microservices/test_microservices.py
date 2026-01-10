#!/usr/bin/env python3
"""Test script for microservices architecture"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_test(name, passed, details=""):
    status = "✅" if passed else "❌"
    print(f"{status} {name}")
    if details:
        print(f"   {details}")

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()

        all_healthy = (
            data["status"] in ["healthy", "degraded"] and
            data["services"]["agent"]["status"] == "healthy" and
            data["services"]["task"]["status"] == "healthy" and
            data["services"]["memory"]["status"] == "healthy"
        )

        print_test("Health Check", all_healthy,
                  f"Gateway: {data['status']}, Services: {len(data['services'])} healthy")
        return all_healthy
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False

def test_create_agent():
    """Test creating an agent"""
    try:
        agent_data = {
            "name": "Test Agent",
            "model": "ollama/llama3.2",
            "role": "assistant",
            "goal": "Test microservices",
            "instructions": "Be helpful",
            "enable_memory": False
        }

        response = requests.post(f"{BASE_URL}/agents", json=agent_data)
        data = response.json()

        success = response.status_code == 200 and "id" in data
        print_test("Create Agent", success,
                  f"Agent ID: {data.get('id', 'N/A')[:8]}...")
        return data.get("id") if success else None
    except Exception as e:
        print_test("Create Agent", False, str(e))
        return None

def test_list_agents():
    """Test listing agents"""
    try:
        response = requests.get(f"{BASE_URL}/agents")
        data = response.json()

        success = response.status_code == 200 and isinstance(data, list)
        print_test("List Agents", success,
                  f"Found {len(data)} agents")
        return success
    except Exception as e:
        print_test("List Agents", False, str(e))
        return False

def test_execute_task(agent_id):
    """Test executing a task"""
    try:
        task_data = {
            "agent_id": agent_id,
            "description": "Say 'Microservices test successful' in Turkish"
        }

        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        data = response.json()

        success = response.status_code == 200 and data.get("status") == "completed"
        exec_time = data.get("execution_time_ms", 0)
        print_test("Execute Task", success,
                  f"Completed in {exec_time:.0f}ms")
        return success
    except Exception as e:
        print_test("Execute Task", False, str(e))
        return False

def test_create_session():
    """Test creating a session"""
    try:
        session_data = {
            "session_id": f"test-session-{int(time.time())}",
            "storage_type": "memory"
        }

        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        data = response.json()

        success = response.status_code == 200 and "session_id" in data
        print_test("Create Session", success,
                  f"Session: {data.get('session_id', 'N/A')}")
        return data.get("session_id") if success else None
    except Exception as e:
        print_test("Create Session", False, str(e))
        return None

def test_list_sessions():
    """Test listing sessions"""
    try:
        response = requests.get(f"{BASE_URL}/sessions")
        data = response.json()

        success = response.status_code == 200 and isinstance(data, list)
        print_test("List Sessions", success,
                  f"Found {len(data)} sessions")
        return success
    except Exception as e:
        print_test("List Sessions", False, str(e))
        return False

def main():
    print("\n" + "=" * 60)
    print("🚀 MICROSERVICES ARCHITECTURE TEST")
    print("=" * 60 + "\n")

    print("Testing Gateway and Services...")
    print("-" * 60)

    # Test health
    health_ok = test_health_check()

    if not health_ok:
        print("\n❌ Services are not healthy. Please check if all services are running.")
        return

    print("\nTesting Agent Service...")
    print("-" * 60)

    # Test agent operations
    agent_id = test_create_agent()
    test_list_agents()

    print("\nTesting Task Service...")
    print("-" * 60)

    # Test task execution
    if agent_id:
        test_execute_task(agent_id)
    else:
        print_test("Execute Task", False, "No agent available")

    print("\nTesting Memory Service...")
    print("-" * 60)

    # Test session operations
    session_id = test_create_session()
    test_list_sessions()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
    print(f"\n📊 Admin Panel: http://localhost:8000/admin")
    print(f"🏥 Health Check: http://localhost:8000/health")
    print(f"\n📝 Service URLs:")
    print(f"   - API Gateway:    http://localhost:8000")
    print(f"   - Agent Service:  http://localhost:8001")
    print(f"   - Task Service:   http://localhost:8002")
    print(f"   - Memory Service: http://localhost:8003")
    print()

if __name__ == "__main__":
    main()
