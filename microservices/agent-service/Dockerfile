FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy

# Copy shared code
COPY shared/ /app/shared/

# Copy service code
COPY agent-service/main.py /app/

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
