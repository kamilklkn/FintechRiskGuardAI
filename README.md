# 🛡️ RiskGuard AI - AI-Powered Merchant Risk Scoring System

Yapay zeka destekli, otomatik merchant risk değerlendirme ve skorlama sistemi. Ticari belgeleri OCR ile okuyup analiz eder, risk skorları üretir ve otomatik raporlar gönderir.

## 🌟 Özellikler

- 🤖 **AI-Powered Analysis**: Ollama/llama3.2 ile akıllı risk analizi
- 📄 **OCR Document Processing**: Türkçe belgelerden otomatik veri çıkarma
  - Ticaret Sicil Gazetesi
  - Vergi Levhası
  - MERSIS Belgesi
  - İmza Sirküleri
- 🎯 **Risk Scoring**: Çoklu veri kaynağı ile kapsamlı risk değerlendirme
- 📧 **Automated Reporting**: Risk raporlarının otomatik e-posta gönderimi
- 🏗️ **Microservices Architecture**: 6 bağımsız servis
- 💾 **Session Management**: Konuşma geçmişi ve hafıza yönetimi
- 🌐 **Modern Admin Panel**: Kullanıcı dostu web arayüzü

## 🚀 Hızlı Başlangıç

### Tek Komutla Başlat

```bash
./start.sh
```

Bu komut otomatik olarak:
- ✅ Virtual environment oluşturur/aktifleştirir
- ✅ Gerekli Python paketlerini yükler
- ✅ Tesseract OCR'ı kontrol eder/yükler
- ✅ Ollama servisini başlatır
- ✅ llama3.2 modelini indirir (yoksa)
- ✅ 6 microservisi başlatır
- ✅ Tarayıcıda admin panelini açar

### Admin Paneline Erişim
```
http://localhost:8000
```

### Durdurma

```bash
./stop.sh
```

## 📋 Gereksinimler

- macOS (Apple Silicon veya Intel)
- Python 3.8+
- Homebrew package manager

*Not: `start.sh` scripti tüm gereksinimleri otomatik yükler*

## 🎯 Ne Yapar?

Merchant (üye işyeri) başvurularını otomatik olarak analiz eder ve risk skorlar:
- ⚡ **15 saniyede** detaylı risk analizi
- 🔍 **8 farklı veri kaynağından** bilgi toplama
- 🤖 **AI agent** ile akıllı değerlendirme
- 📊 **0-100 risk skoru** ve kategori (EXCELLENT, LOW, MEDIUM, HIGH, CRITICAL)
- 📧 **Otomatik HTML rapor** 4 departmana (Risk, Uyum, Fraud, Product)
- 🔒 **Tamamen lokal** - API key gerektirmez, KVKK/GDPR uyumlu

## ✨ Öne Çıkan Özellikler

### 🤖 AI-Powered Risk Analysis
- **Ollama/llama3.2** ile lokal LLM kullanımı
- Tool calling ile akıllı veri toplama
- MERSIS, Vergi Dairesi, Ticaret Sicili, BKM, Web kontrolü
- Fraud database ve website güvenlik analizi

### 🏗️ Enterprise-Grade Architecture
- **Microservices**: 6 bağımsız servis
- **Scalable**: Her servis ayrı ölçeklendirilebilir
- **Fault Tolerant**: Bir servis çökse diğerleri çalışır
- **API Gateway**: Merkezi routing ve yük dengeleme

### 📊 Comprehensive Reporting
- Real-time risk scoring dashboard
- Beautiful HTML email reports
- Detailed source breakdown
- Actionable recommendations

### 🔧 Developer Friendly
- **Modern Stack**: FastAPI, Python 3.9+, async/await
- **Type Safe**: Pydantic models everywhere
- **Well Documented**: Comprehensive guides
- **Easy Setup**: 5 dakikada çalıştır

## 🏗️ Architecture

```
                  ┌─────────────────────────┐
                  │  Admin Panel (Web UI)   │
                  └────────────┬────────────┘
                               │
                  ┌────────────▼────────────┐
                  │   API Gateway (8000)     │
                  │   Routing + Auth         │
                  └─────┬──────────┬─────────┘
                        │          │
        ┌───────────────┼──────────┼─────────────┐
        │               │          │             │
   ┌────▼────┐    ┌────▼─────┐  ┌▼────────┐  ┌─▼──────┐
   │ Risk    │    │  Email   │  │ Agent/  │  │ Memory │
   │ Service │    │  Service │  │ Task    │  │ Service│
   │  :8004  │    │  :8005   │  │ Services│  │ :8003  │
   └────┬────┘    └──────────┘  └─────────┘  └────────┘
        │
   ┌────▼────────┐
   │ AI Agent    │
   │ (Ollama)    │
   │             │
   │ • MERSIS    │
   │ • Tax DB    │
   │ • Trade Reg │
   │ • BKM       │
   │ • Web Check │
   │ • Fraud DB  │
   └─────────────┘
```

### Microservices

| Service | Port | Görev | AI? |
|---------|------|-------|-----|
| **API Gateway** | 8000 | Request routing, admin panel | - |
| **Agent Service** | 8001 | AI agent management | - |
| **Task Service** | 8002 | Task execution | - |
| **Memory Service** | 8003 | Session & message storage | - |
| **Risk Service** | 8004 | ⭐ Risk scoring & analysis | ✅ AI |
| **Email Service** | 8005 | HTML report delivery | - |

## 📦 Installation

### Prerequisites

- Python 3.9+
- Ollama (for local LLM support)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Local_Agent_Fremework
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -e .
```

4. Install Ollama and pull a model:
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2
```

## 🎯 Quick Start

### Start All Services

```bash
cd microservices
python3 run_all.py
```

This will start all 4 microservices:
- Agent Service (8001)
- Task Service (8002)
- Memory Service (8003)
- API Gateway (8000)

### Access Admin Panel

Open your browser and go to:
```
http://localhost:8000/admin
```

### Run Tests

```bash
cd microservices
source ../venv/bin/activate
python test_microservices.py
```

### Stop Services

```bash
cd microservices
./stop-services.sh
```

## 🔧 Usage

### API Examples

#### Create an Agent

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Assistant",
    "model": "ollama/llama3.2",
    "role": "assistant",
    "goal": "Help users with their questions",
    "instructions": "Be helpful and concise"
  }'
```

#### Execute a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "YOUR_AGENT_ID",
    "description": "Explain quantum computing in simple terms"
  }'
```

#### Create a Session

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session",
    "storage_type": "memory"
  }'
```

### Python SDK Usage

```python
from local_agent_framework import Agent, Task

# Create an agent
agent = Agent(
    model="ollama/llama3.2",
    name="My Assistant",
    role="assistant",
    goal="Help users"
)

# Create and execute a task
task = Task(description="What is the weather like?")
result = agent.do(task)

print(result.result)
```

## 📊 Health Check

Check if all services are running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
    "service": "gateway",
    "status": "healthy",
    "services": {
        "agent": {"status": "healthy"},
        "task": {"status": "healthy"},
        "memory": {"status": "healthy"}
    }
}
```

## 📁 Project Structure

```
Local_Agent_Fremework/
├── microservices/              # Microservices architecture
│   ├── gateway/                # API Gateway
│   ├── agent-service/          # Agent management
│   ├── task-service/           # Task execution
│   ├── memory-service/         # Memory & sessions
│   ├── shared/                 # Shared utilities
│   │   ├── models.py           # Pydantic models
│   │   └── database.py         # Database config
│   ├── run_all.py              # Start all services
│   ├── stop-services.sh        # Stop all services
│   ├── test_microservices.py   # Test suite
│   └── README.md               # Microservices docs
├── local_agent_framework/      # Core framework
│   ├── core/                   # Core components
│   │   ├── agent.py            # Agent class
│   │   ├── task.py             # Task class
│   │   ├── memory.py           # Memory management
│   │   └── tools.py            # Tool system
│   └── __init__.py
├── examples/                   # Usage examples
├── ARCHITECTURE.md             # Architecture design
├── MICROSERVICES_ARCHITECTURE.md  # Microservices design
├── MICROSERVICES_SETUP.md      # Detailed setup guide
└── README.md                   # This file
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Pydantic, SQLAlchemy
- **Database**: SQLite (dev), PostgreSQL (prod)
- **LLM Providers**: OpenAI, Anthropic, Ollama
- **HTTP Client**: HTTPX (async)
- **Server**: Uvicorn (ASGI)
- **Frontend**: Vanilla JS, HTML5, CSS3

## 🌟 Key Features

### Microservices Benefits

✅ **Scalability**: Each service scales independently
✅ **Maintainability**: Clean separation of concerns
✅ **Fault Isolation**: Service failures don't cascade
✅ **Technology Flexibility**: Use best tool for each service
✅ **Independent Deployment**: Deploy services separately
✅ **Team Autonomy**: Teams own their services

### Framework Features

✅ **Multi-LLM Support**: OpenAI, Anthropic, Ollama
✅ **Memory System**: Conversation history and context
✅ **Tool Integration**: Extensible tool system
✅ **Admin Panel**: Web-based management interface
✅ **RESTful API**: Complete REST API
✅ **Database Persistence**: SQLAlchemy ORM
✅ **Health Checks**: Service monitoring
✅ **CORS Support**: Cross-origin requests

## 📖 Documentation

- **[Microservices Setup](MICROSERVICES_SETUP.md)**: Detailed setup and usage guide
- **[Architecture Design](ARCHITECTURE.md)**: System architecture and patterns
- **[Microservices Architecture](MICROSERVICES_ARCHITECTURE.md)**: Microservices design
- **[Microservices README](microservices/README.md)**: Quick start guide

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd microservices
source ../venv/bin/activate
python test_microservices.py
```

Test coverage:
- Health checks for all services
- Agent CRUD operations
- Task execution
- Session management
- API Gateway routing

## 🔐 Configuration

### Environment Variables

```bash
# Database
export DATABASE_URL="sqlite:///./microservices.db"

# Service URLs (for Gateway)
export AGENT_SERVICE_URL="http://localhost:8001"
export TASK_SERVICE_URL="http://localhost:8002"
export MEMORY_SERVICE_URL="http://localhost:8003"

# LLM API Keys (optional)
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

## 🚀 Production Deployment

### Docker (Coming Soon)

```bash
docker-compose up -d
```

### Kubernetes (Coming Soon)

```bash
kubectl apply -f k8s/
```

## 🔜 Roadmap

- [x] Microservices architecture
- [x] Admin panel
- [x] Health checks
- [x] Database persistence
- [ ] Docker containerization
- [ ] Kubernetes orchestration
- [ ] Message queue (RabbitMQ)
- [ ] Authentication (JWT)
- [ ] Monitoring (Prometheus, Grafana)
- [ ] API rate limiting
- [ ] Circuit breaker pattern
- [ ] Service mesh (Istio)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 🐛 Troubleshooting

### Port Already in Use

```bash
lsof -ti:8000 | xargs kill -9
```

### Services Not Starting

1. Activate virtual environment:
```bash
source venv/bin/activate
```

2. Check dependencies:
```bash
pip install -r requirements.txt
```

3. Check if Ollama is running:
```bash
ollama list
```

### Import Errors

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/microservices"
```

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the examples

## ⭐ Acknowledgments

Built with modern microservices architecture patterns and best practices.

---

**Version**: 1.0.0 (Microservices Edition)
**Last Updated**: 2026-01-10
