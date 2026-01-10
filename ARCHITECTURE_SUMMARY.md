# Mimari Özet - Hızlı Referans

## 🎯 Ana Prensipler

### 1. Katmanlı Mimari (Layered Architecture)
```
Presentation Layer (API)
    ↓
Business Logic Layer (Services)
    ↓
Data Access Layer (Repositories)
    ↓
Infrastructure Layer (Database, Cache, etc.)
```

### 2. Dependency Inversion
- Üst katmanlar alt katmanlara doğrudan bağımlı değil
- Interface'ler üzerinden iletişim
- Dependency Injection ile bağımlılıkları yönet

### 3. Separation of Concerns
- Her modül tek bir sorumluluğa sahip
- Business logic API'den ayrı
- Infrastructure business logic'den ayrı

## 📂 Klasör Yapısı Özeti

```
project/
├── api/              # HTTP endpoints, routing, validation
├── core/             # Business logic, domain models
├── infrastructure/   # External services, DB, cache
├── workers/          # Background tasks
├── config/           # Settings, environment
└── tests/            # All tests
```

## 🔑 Temel Kavramlar

### Repository Pattern
```python
# Data access logic'i encapsulate eder
class AgentRepository:
    def get(self, id) → Agent
    def create(self, data) → Agent
    def update(self, id, data) → Agent
    def delete(self, id) → bool
```

### Service Pattern
```python
# Business logic'i içerir
class AgentService:
    def __init__(self, repo, cache):
        self.repo = repo
        self.cache = cache

    async def create_agent(self, user_id, name, model):
        # Validation
        # Business rules
        # Cache invalidation
        # Logging
        return agent
```

### Dependency Injection
```python
# FastAPI dependencies
def get_agent_service(db: Session = Depends(get_db)):
    repo = AgentRepository(db)
    cache = CacheService()
    return AgentService(repo, cache)

# Usage in endpoint
@router.post("/agents")
async def create(
    data: AgentCreate,
    service: AgentService = Depends(get_agent_service)
):
    return await service.create(data)
```

## 🗄️ Database Stratejisi

### ORM (SQLAlchemy)
```python
# Model tanımı
class Agent(Base):
    __tablename__ = "agents"
    id = Column(UUID, primary_key=True)
    name = Column(String)
    user = relationship("User")

# Query
agent = db.query(Agent).filter(Agent.id == id).first()
```

### Migrations (Alembic)
```bash
# Yeni migration
alembic revision --autogenerate -m "message"

# Migration uygula
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🔐 Authentication Flow

```
1. User login → POST /auth/login
2. Server validates credentials
3. Server generates JWT token
4. Client stores token
5. Client sends token in header: Authorization: Bearer <token>
6. Server validates token
7. Server extracts user info
8. Request processed
```

## 📊 Caching Strategy

```
Level 1: In-memory cache (process-local)
    ↓ Miss
Level 2: Redis cache (shared)
    ↓ Miss
Level 3: Database
    ↑ Store
    ↑ Store
```

## 🚀 Deployment Flow

```
Code → Git Push
    ↓
GitHub Actions (CI)
    ├── Lint (ruff, black)
    ├── Type check (mypy)
    └── Tests (pytest)
    ↓ (if main branch)
Docker Build
    ↓
Push to Registry
    ↓
Deploy to K8s / Cloud
    ↓
Health check
    ↓
Traffic switch (zero downtime)
```

## 🧪 Testing Piramidi

```
       E2E Tests (az)
      /              \
   Integration Tests
  /                  \
Unit Tests (çok)
```

### Test Tipleri
- **Unit**: Tek fonksiyon/method, mock dependencies
- **Integration**: Birden fazla component, gerçek DB
- **E2E**: Tam kullanıcı akışı, tüm sistem

## 📈 Monitoring Stack

```
Application
    ↓
Metrics → Prometheus → Grafana
Logs → structlog → ELK/Loki
Traces → OpenTelemetry → Jaeger
Errors → Sentry
```

## 🔧 Environment Management

```
Development:
  - SQLite/Local Postgres
  - In-memory cache
  - Debug logging
  - Auto-reload

Staging:
  - Postgres (small)
  - Redis
  - Info logging
  - Mirror production

Production:
  - Postgres (cluster)
  - Redis (cluster)
  - Warning logging
  - High availability
```

## 📦 Dependency Stack

### Core
- FastAPI: Web framework
- Pydantic: Data validation
- SQLAlchemy: ORM
- Alembic: Migrations

### Infrastructure
- PostgreSQL: Primary database
- Redis: Cache & sessions
- Celery/RQ: Task queue
- S3/MinIO: File storage

### Monitoring
- Prometheus: Metrics
- Grafana: Visualization
- structlog: Logging
- Sentry: Error tracking

### DevOps
- Docker: Containerization
- Kubernetes: Orchestration
- GitHub Actions: CI/CD
- Nginx: Reverse proxy

## 🎯 Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| API Response | < 100ms (p95) | < 500ms |
| DB Query | < 50ms (p95) | < 200ms |
| Cache Hit | < 10ms | < 50ms |
| Uptime | 99.9% | 99% |
| Error Rate | < 0.1% | < 1% |

## 🔒 Security Checklist

- [ ] HTTPS everywhere
- [ ] JWT with short expiry
- [ ] Password hashing (bcrypt)
- [ ] Rate limiting
- [ ] Input validation
- [ ] SQL injection prevention (ORM)
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Security headers
- [ ] Regular dependency updates
- [ ] Secrets in environment variables
- [ ] Audit logging

## 📋 Daily Operations

### Deploy yeni versiyon
```bash
git tag v2.0.1
git push --tags
# CI/CD automatically deploys
```

### Database migration
```bash
alembic revision --autogenerate -m "add field"
alembic upgrade head
```

### Check logs
```bash
kubectl logs -f deployment/agent-api
# or
docker-compose logs -f api
```

### Scale up/down
```bash
kubectl scale deployment agent-api --replicas=5
# or
docker-compose up -d --scale api=3
```

### Rollback
```bash
kubectl rollout undo deployment/agent-api
# or
alembic downgrade -1
```

## 🐛 Common Issues

### "Database connection failed"
```bash
# Check database is running
docker-compose ps db

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

### "Redis connection timeout"
```bash
# Check Redis
redis-cli ping

# Check Redis URL
echo $REDIS_URL
```

### "High memory usage"
```bash
# Check metrics
curl http://localhost:8000/metrics

# Scale up
kubectl scale deployment agent-api --replicas=5
```

## 📚 Quick Commands

```bash
# Start development
docker-compose up -d
uvicorn api.main:app --reload

# Run tests
pytest -v --cov

# Lint & format
ruff check .
black .

# Database migration
alembic upgrade head

# Create admin user
python scripts/create_admin.py

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api

# Stop everything
docker-compose down
```

## 🎓 Best Practices

1. **Always use migrations** - Never manually alter database
2. **Write tests first** - TDD approach
3. **Keep dependencies updated** - Security patches
4. **Use environment variables** - Never hardcode secrets
5. **Log everything important** - Structured logging
6. **Monitor proactively** - Set up alerts
7. **Document as you go** - Update docs with code
8. **Review before merge** - Code review required
9. **Small PRs** - Easier to review
10. **Semantic versioning** - v2.1.3 (major.minor.patch)

## 🔗 Useful Links

- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Admin Panel: http://localhost:8000/admin
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## 💡 Pro Tips

1. Use `@lru_cache()` for expensive pure functions
2. Batch database queries to reduce round trips
3. Use Redis for frequently accessed data
4. Async all the way (avoid blocking operations)
5. Index database columns used in WHERE/JOIN
6. Use connection pooling for databases
7. Compress API responses (gzip)
8. Use CDN for static assets
9. Implement pagination for large lists
10. Use background tasks for heavy operations

---

**Remember**:
- Start simple, scale when needed
- Measure before optimizing
- Security is not optional
- Documentation is part of code
