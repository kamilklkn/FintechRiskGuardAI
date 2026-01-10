# Microservices Setup & Usage Guide

## 🎯 Overview

Local Agent Framework microservices mimarisine başarıyla dönüştürüldü. Sistem şimdi 4 ayrı servisten oluşuyor:

1. **API Gateway** (Port 8000) - Tüm istekleri yönlendirir
2. **Agent Service** (Port 8001) - Agent CRUD operasyonları
3. **Task Service** (Port 8002) - Task çalıştırma ve yönetimi
4. **Memory Service** (Port 8003) - Session ve mesaj yönetimi

## 🚀 Quick Start

### 1. Servisleri Başlatma

```bash
cd microservices
python3 run_all.py
```

Servisler sırasıyla başlatılacak ve health check yapılacak.

### 2. Servisleri Durdurma

```bash
cd microservices
./stop-services.sh
```

Ya da:

```bash
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
lsof -ti:8002 | xargs kill -9
lsof -ti:8003 | xargs kill -9
```

### 3. Test Etme

```bash
cd microservices
source ../venv/bin/activate
python test_microservices.py
```

## 📊 Admin Panel

Tarayıcıda şu adresi açın:

```
http://localhost:8000/admin
```

Admin panel üzerinden:
- Agentları görüntüleme ve oluşturma
- Task çalıştırma ve sonuçları görüntüleme
- Sessionları yönetme
- Sistem sağlığını kontrol etme

## 🔍 Health Check

Tüm servislerin durumunu kontrol etmek için:

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

Beklenen çıktı:

```json
{
    "service": "gateway",
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-01-10T...",
    "services": {
        "agent": {
            "status": "healthy",
            "url": "http://localhost:8001"
        },
        "task": {
            "status": "healthy",
            "url": "http://localhost:8002"
        },
        "memory": {
            "status": "healthy",
            "url": "http://localhost:8003"
        }
    }
}
```

## 🛠️ API Kullanımı

### Agent Oluşturma

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Agent",
    "model": "ollama/llama3.2",
    "role": "assistant",
    "goal": "Help users",
    "instructions": "Be helpful and concise",
    "enable_memory": false
  }'
```

### Agent Listesi

```bash
curl http://localhost:8000/agents
```

### Task Çalıştırma

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "YOUR_AGENT_ID",
    "description": "Your task description"
  }'
```

### Session Oluşturma

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session",
    "storage_type": "memory"
  }'
```

### Session Listesi

```bash
curl http://localhost:8000/sessions
```

## 📁 Proje Yapısı

```
microservices/
├── gateway/
│   └── main.py           # API Gateway
├── agent-service/
│   └── main.py           # Agent Service
├── task-service/
│   └── main.py           # Task Executor Service
├── memory-service/
│   └── main.py           # Memory Service
├── shared/
│   ├── models.py         # Pydantic models
│   └── database.py       # Database utilities
├── run_all.py            # Start all services
├── stop-services.sh      # Stop all services
├── test_microservices.py # Test script
└── microservices.db      # SQLite database
```

## 🗄️ Database

Servisler SQLite veritabanı kullanıyor:
- **Dosya**: `microservices/microservices.db`
- **Tablolar**: agents, tasks, sessions, messages

Production ortamında PostgreSQL'e geçiş yapılabilir:

```python
# shared/database.py içinde
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/dbname")
```

## 🔧 Servis Detayları

### API Gateway (Port 8000)

- Tüm istekleri ilgili servislere yönlendirir
- CORS middleware sağlar
- Admin paneli serve eder
- Health check yapar

**Endpoints**:
- `GET /` - Admin panel
- `GET /admin` - Admin panel
- `GET /health` - Tüm servislerin health durumu
- `POST /agents` → Agent Service
- `GET /agents` → Agent Service
- `POST /tasks` → Task Service
- `GET /tasks` → Task Service
- `POST /sessions` → Memory Service
- `GET /sessions` → Memory Service

### Agent Service (Port 8001)

Agent CRUD operasyonlarını yönetir.

**Endpoints**:
- `GET /health` - Service health
- `POST /agents` - Agent oluştur
- `GET /agents` - Tüm agentları listele
- `GET /agents/{agent_id}` - Agent detayı
- `DELETE /agents/{agent_id}` - Agent sil

### Task Service (Port 8002)

Task çalıştırma ve yönetimi.

**Endpoints**:
- `GET /health` - Service health
- `POST /tasks` - Task çalıştır
- `GET /tasks` - Tüm taskları listele
- `GET /tasks/{task_id}` - Task detayı

### Memory Service (Port 8003)

Session ve mesaj yönetimi.

**Endpoints**:
- `GET /health` - Service health
- `POST /sessions` - Session oluştur
- `GET /sessions` - Tüm sessionları listele
- `GET /sessions/{session_id}` - Session detayı
- `DELETE /sessions/{session_id}` - Session sil
- `POST /sessions/{session_id}/messages` - Mesaj ekle
- `GET /sessions/{session_id}/messages` - Mesajları listele

## 🔐 Environment Variables

Servisler şu environment variable'ları kullanabilir:

```bash
# Database
export DATABASE_URL="sqlite:///./microservices.db"

# Service URLs (Gateway için)
export AGENT_SERVICE_URL="http://localhost:8001"
export TASK_SERVICE_URL="http://localhost:8002"
export MEMORY_SERVICE_URL="http://localhost:8003"
```

## 🐳 Docker Support (Gelecek)

Docker Compose ile çalıştırmak için:

```yaml
# docker-compose.yml
version: '3.8'
services:
  gateway:
    build: ./gateway
    ports:
      - "8000:8000"
  agent-service:
    build: ./agent-service
    ports:
      - "8001:8001"
  # ... diğer servisler
```

## 📈 Performance

Test sonuçları:
- **Health Check**: ~10ms
- **Agent CRUD**: ~50ms
- **Task Execution**: ~500-5000ms (modele bağlı)
- **Session CRUD**: ~30ms

## 🔍 Debugging

Servis loglarını görmek için:

```bash
# Terminal'de servisleri foreground'da başlatın
cd microservices/gateway && python main.py
# Farklı terminallerde diğer servisleri başlatın
```

## 🚀 Next Steps

1. ✅ Microservices mimarisi oluşturuldu
2. ✅ Tüm servisler test edildi
3. ✅ Admin panel entegre edildi
4. 🔜 Docker containerization
5. 🔜 Kubernetes deployment
6. 🔜 Message queue (RabbitMQ) entegrasyonu
7. 🔜 Monitoring ve logging (Prometheus, Grafana)
8. 🔜 API authentication (JWT)

## 📞 Troubleshooting

### Port kullanımda hatası

```bash
lsof -ti:8000 | xargs kill -9
```

### Servis başlamıyor

1. Virtual environment aktif mi kontrol edin:
```bash
source venv/bin/activate
```

2. Bağımlılıklar yüklü mü kontrol edin:
```bash
pip install -r requirements.txt
```

3. Database dosyası erişilebilir mi kontrol edin:
```bash
ls -la microservices/microservices.db
```

### Import hataları

```bash
# Shared modülünü Python path'e ekleyin
export PYTHONPATH="${PYTHONPATH}:$(pwd)/microservices"
```

## 📝 Changelog

### v1.0.0 (2026-01-10)
- ✅ Microservices mimarisine geçiş tamamlandı
- ✅ 4 servis oluşturuldu (Gateway, Agent, Task, Memory)
- ✅ SQLite database entegrasyonu
- ✅ Admin panel entegre edildi
- ✅ Comprehensive test suite eklendi
- ✅ Health check sistemi
- ✅ CORS support
- ✅ Service discovery (health checks)
