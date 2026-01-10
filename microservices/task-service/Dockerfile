FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy httpx ollama

# Copy framework
COPY ../local_agent_framework/ /app/local_agent_framework/

# Copy shared code
COPY shared/ /app/shared/

# Copy service code
COPY task-service/main.py /app/

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
