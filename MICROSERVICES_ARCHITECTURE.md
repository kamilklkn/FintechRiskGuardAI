# Microservices Architecture Design

## 🏗️ Service Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (Port 8000)                  │
│              Route requests to microservices                 │
└────────┬────────────┬────────────┬────────────┬─────────────┘
         │            │            │            │
    ┌────▼────┐  ┌───▼────┐  ┌───▼─────┐  ┌──▼──────┐
    │ Agent   │  │ Task   │  │ Memory  │  │ Auth    │
    │ Service │  │ Exec   │  │ Service │  │ Service │
    │ :8001   │  │ :8002  │  │ :8003   │  │ :8004   │
    └────┬────┘  └───┬────┘  └───┬─────┘  └──┬──────┘
         │            │            │            │
         └────────────┴────────────┴────────────┘
                      │
              ┌───────▼────────┐
              │  Message Queue │
              │  (RabbitMQ)    │
              │    :5672       │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │   PostgreSQL   │
              │     :5432      │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │     Redis      │
              │     :6379      │
              └────────────────┘
```

## 📦 Services

### 1. API Gateway (Port 8000)
**Responsibility**: Request routing, rate limiting, authentication
- Routes to appropriate microservice
- Handles CORS
- JWT validation
- Rate limiting
- Request/response logging

### 2. Agent Service (Port 8001)
**Responsibility**: Agent CRUD operations
- Create/Read/Update/Delete agents
- Agent configuration management
- Agent status tracking
- Database: agents table

### 3. Task Executor Service (Port 8002)
**Responsibility**: Execute agent tasks
- Receive task execution requests
- Interact with LLM providers
- Store task results
- Async execution via message queue
- Database: tasks table

### 4. Memory Service (Port 8003)
**Responsibility**: Session and memory management
- Session CRUD
- Message history
- Context management
- Database: sessions, messages tables

### 5. Auth Service (Port 8004)
**Responsibility**: Authentication and authorization
- User management
- JWT token generation/validation
- API key management
- Database: users, api_keys tables

## 🔄 Communication Patterns

### Synchronous (HTTP/REST)
- API Gateway ↔ Services
- Frontend ↔ API Gateway

### Asynchronous (Message Queue)
- Task execution (long-running)
- Background jobs
- Event notifications

## 🗄️ Database Strategy

### Database per Service (Recommended)
```
agent-service-db     (agents table)
task-service-db      (tasks table)
memory-service-db    (sessions, messages)
auth-service-db      (users, api_keys)
```

### Shared Database (Simpler for MVP)
```
shared-db
  ├── agents
  ├── tasks
  ├── sessions
  ├── messages
  └── users
```

## 📊 Technology Stack

- **API Gateway**: FastAPI + HTTP reverse proxy
- **Services**: FastAPI (microservices)
- **Message Queue**: RabbitMQ
- **Database**: PostgreSQL
- **Cache**: Redis
- **Container**: Docker
- **Orchestration**: Docker Compose (dev), Kubernetes (prod)
- **Service Discovery**: Consul / etcd (production)

## 🔐 Security

- JWT tokens (Auth Service)
- API Gateway validates all requests
- Service-to-service communication via internal network
- Secrets in environment variables
