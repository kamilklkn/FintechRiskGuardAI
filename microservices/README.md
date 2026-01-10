# Local Agent Framework - Microservices

Bu klasör Local Agent Framework'ün microservices mimarisini içerir.

## 🚀 Hızlı Başlangıç

### Servisleri Başlat

```bash
python3 run_all.py
```

### Test Et

```bash
source ../venv/bin/activate
python test_microservices.py
```

### Servisleri Durdur

```bash
./stop-services.sh
```

## 📊 Servisler

| Servis | Port | Açıklama |
|--------|------|----------|
| API Gateway | 8000 | Ana giriş noktası, routing |
| Agent Service | 8001 | Agent CRUD operasyonları |
| Task Service | 8002 | Task çalıştırma |
| Memory Service | 8003 | Session ve mesaj yönetimi |

## 🌐 Erişim

- **Admin Panel**: http://localhost:8000/admin
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

## 📖 Detaylı Dokümantasyon

Detaylı kullanım bilgisi için [MICROSERVICES_SETUP.md](../MICROSERVICES_SETUP.md) dosyasına bakın.

## ✅ Test Sonuçları

```
✅ Health Check - Gateway: healthy, Services: 3 healthy
✅ Create Agent - Agent ID: 76fccdb3...
✅ List Agents - Found 3 agents
✅ Execute Task - Completed in 556ms
✅ Create Session - Session: test-session-1768056827
✅ List Sessions - Found 2 sessions
```

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (Port 8000)                  │
│              Route requests to microservices                 │
└────────┬────────────┬────────────┬────────────┬─────────────┘
         │            │            │            │
    ┌────▼────┐  ┌───▼────┐  ┌───▼─────┐  ┌──▼──────┐
    │ Agent   │  │ Task   │  │ Memory  │  │ Admin   │
    │ Service │  │ Service│  │ Service │  │ Panel   │
    │ :8001   │  │ :8002  │  │ :8003   │  │ (Static)│
    └─────────┘  └────────┘  └─────────┘  └─────────┘
```

## 🛠️ Teknolojiler

- **FastAPI**: Modern, high-performance web framework
- **SQLAlchemy**: ORM ve database management
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
- **HTTPX**: Async HTTP client (servisler arası iletişim)
- **SQLite**: Development database

## 📝 API Örnekleri

### Agent Oluştur

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "My Agent", "model": "ollama/llama3.2", "role": "assistant"}'
```

### Task Çalıştır

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "AGENT_ID", "description": "Your task"}'
```

## 🔧 Geliştirme

Her servisi ayrı ayrı çalıştırmak için:

```bash
# Terminal 1
cd agent-service && python main.py

# Terminal 2
cd task-service && python main.py

# Terminal 3
cd memory-service && python main.py

# Terminal 4
cd gateway && python main.py
```

## 📦 Dosya Yapısı

```
microservices/
├── gateway/              # API Gateway
├── agent-service/        # Agent CRUD
├── task-service/         # Task execution
├── memory-service/       # Session & messages
├── shared/               # Shared utilities
│   ├── models.py         # Pydantic models
│   └── database.py       # Database config
├── run_all.py            # Start script
├── stop-services.sh      # Stop script
├── test_microservices.py # Test suite
└── microservices.db      # SQLite database
```
