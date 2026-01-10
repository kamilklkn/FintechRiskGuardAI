#!/usr/bin/env python3
"""Start all microservices"""
import subprocess
import time
import sys
import os

# Use venv python
venv_python = os.path.join(os.path.dirname(__file__), '..', 'venv', 'bin', 'python')

services = [
    ("Agent Service", "agent-service/main.py", 8001),
    ("Task Service", "task-service/main.py", 8002),
    ("Memory Service", "memory-service/main.py", 8003),
    ("Risk Scoring Service", "risk-service/main.py", 8004),
    ("Email Service", "email-service/main.py", 8005),
    ("API Gateway", "gateway/main.py", 8000),
]

processes = []

print("Starting all microservices...")
print("=" * 60)

for name, path, port in services:
    print(f"Starting {name} on port {port}...")
    proc = subprocess.Popen(
        [venv_python, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    processes.append((name, proc, port))
    time.sleep(2)

print("=" * 60)
print("\n✅ All services started!\n")
print("Service URLs:")
for name, proc, port in processes:
    print(f"  {name:20} http://localhost:{port}")

print("\nAdmin Panel:     http://localhost:8000/admin")
print("Health Check:    http://localhost:8000/health")
print("\nPress Ctrl+C to stop all services")

try:
    while True:
        time.sleep(1)
        # Check if any process died
        for name, proc, port in processes:
            if proc.poll() is not None:
                print(f"\n❌ {name} stopped unexpectedly!")
                stdout, stderr = proc.communicate()
                if stderr:
                    print(f"Error: {stderr.decode()}")
except KeyboardInterrupt:
    print("\n\nStopping all services...")
    for name, proc, port in processes:
        proc.terminate()
    print("✅ All services stopped")
