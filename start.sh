#!/bin/bash

# RiskGuard AI - Proje Başlatma Scripti
# Tüm servisleri ve gerekli bağımlılıkları başlatır

set -e  # Hata durumunda durdur

# Renkli çıktı için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║                                                       ║"
echo "║         🛡️  RiskGuard AI - Başlatılıyor...          ║"
echo "║    AI-Powered Merchant Risk Scoring System           ║"
echo "║                                                       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Proje dizinine git
PROJECT_DIR="/Users/kamilkalkan/www_localhost/Local_Agent_Fremework"
cd "$PROJECT_DIR"

echo -e "${BLUE}📁 Proje dizini: $PROJECT_DIR${NC}\n"

# 1. Python Virtual Environment Kontrolü
echo -e "${YELLOW}[1/6] 🐍 Python Virtual Environment Kontrol Ediliyor...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment bulunamadı. Oluşturuluyor...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment oluşturuldu${NC}"
else
    echo -e "${GREEN}✅ Virtual environment mevcut${NC}"
fi

# Virtual environment'ı aktifleştir
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment aktif${NC}\n"

# 2. Bağımlılıkları Kontrol Et ve Yükle
echo -e "${YELLOW}[2/6] 📦 Python Bağımlılıkları Kontrol Ediliyor...${NC}"
if [ -f "requirements.txt" ]; then
    echo "Bağımlılıklar yükleniyor..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Python bağımlılıkları yüklendi${NC}\n"
else
    echo -e "${YELLOW}⚠️  requirements.txt bulunamadı${NC}\n"
fi

# 3. Tesseract OCR Kontrolü
echo -e "${YELLOW}[3/6] 🔍 Tesseract OCR Kontrol Ediliyor...${NC}"
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -1)
    echo -e "${GREEN}✅ Tesseract kurulu: $TESSERACT_VERSION${NC}"

    # Türkçe dil paketi kontrolü
    if tesseract --list-langs 2>&1 | grep -q "tur"; then
        echo -e "${GREEN}✅ Türkçe dil paketi mevcut${NC}\n"
    else
        echo -e "${YELLOW}⚠️  Türkçe dil paketi bulunamadı. Yükleniyor...${NC}"
        brew install tesseract-lang
        echo -e "${GREEN}✅ Türkçe dil paketi yüklendi${NC}\n"
    fi
else
    echo -e "${RED}❌ Tesseract bulunamadı. Yükleniyor...${NC}"
    brew install tesseract tesseract-lang
    echo -e "${GREEN}✅ Tesseract yüklendi${NC}\n"
fi

# 4. Ollama Kontrolü ve Başlatma
echo -e "${YELLOW}[4/6] 🤖 Ollama AI Kontrol Ediliyor...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama kurulu${NC}"

    # Ollama servisinin çalışıp çalışmadığını kontrol et
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✅ Ollama servisi zaten çalışıyor${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama servisi başlatılıyor...${NC}"
        nohup ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
        echo -e "${GREEN}✅ Ollama servisi başlatıldı${NC}"
    fi

    # llama3.2 modelini kontrol et
    if ollama list | grep -q "llama3.2"; then
        echo -e "${GREEN}✅ llama3.2 modeli mevcut${NC}\n"
    else
        echo -e "${YELLOW}⚠️  llama3.2 modeli bulunamadı. İndiriliyor (bu biraz zaman alabilir)...${NC}"
        ollama pull llama3.2
        echo -e "${GREEN}✅ llama3.2 modeli indirildi${NC}\n"
    fi
else
    echo -e "${RED}❌ Ollama kurulu değil!${NC}"
    echo -e "${YELLOW}Lütfen şu komutu çalıştırın: brew install ollama${NC}\n"
    exit 1
fi

# 5. Önceki Servisleri Temizle
echo -e "${YELLOW}[5/6] 🧹 Önceki Servisler Temizleniyor...${NC}"
# Port 8000-8005 arasındaki tüm servisleri durdur
for port in 8000 8001 8002 8003 8004 8005; do
    PID=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        kill -9 $PID 2>/dev/null && echo -e "${GREEN}✅ Port $port temizlendi${NC}"
    fi
done
echo ""

# 6. Microservisleri Başlat
echo -e "${YELLOW}[6/6] 🚀 Microservisler Başlatılıyor...${NC}\n"

cd microservices

# Her servisi ayrı ayrı başlat
declare -a services=("gateway:8000" "agent-service:8001" "task-service:8002" "memory-service:8003" "risk-service:8004" "email-service:8005")

for service_info in "${services[@]}"; do
    IFS=':' read -r service port <<< "$service_info"
    service_dir="${service//-service/}"
    service_dir="${service_dir//gateway/gateway}"

    echo -e "${BLUE}▶ $service başlatılıyor (Port: $port)...${NC}"

    cd "$service_dir"
    nohup python main.py > "/tmp/$service.log" 2>&1 &
    PID=$!
    echo "$PID" > "/tmp/$service.pid"
    cd ..

    sleep 1
    echo -e "${GREEN}✅ $service başlatıldı (PID: $PID)${NC}"
done

cd ..

# 7. Servislerin Hazır Olmasını Bekle
echo -e "\n${YELLOW}⏳ Servisler başlatılıyor, lütfen bekleyin...${NC}"
sleep 5

# 8. Health Check
echo -e "\n${YELLOW}🏥 Sağlık Kontrolü Yapılıyor...${NC}\n"

GATEWAY_HEALTH=$(curl -s http://localhost:8000/health | grep -o '"status":"healthy"' || echo "")

if [ ! -z "$GATEWAY_HEALTH" ]; then
    echo -e "${GREEN}✅ Gateway Servisi: SAĞLIKLI (http://localhost:8000)${NC}"

    # Detaylı servis durumları
    curl -s http://localhost:8000/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    services = data.get('services', {})
    for name, info in services.items():
        status = info.get('status', 'unknown')
        if status == 'healthy':
            print(f'\033[0;32m  ✅ {name}: SAĞLIKLI\033[0m')
        else:
            print(f'\033[0;31m  ❌ {name}: SORUNLU\033[0m')
except:
    pass
" 2>/dev/null

else
    echo -e "${RED}❌ Gateway Servisi: SORUNLU${NC}"
    echo -e "${YELLOW}Log dosyasını kontrol edin: /tmp/gateway.log${NC}"
fi

# 9. Özet ve Bağlantı Bilgileri
echo -e "\n${PURPLE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                       ║${NC}"
echo -e "${PURPLE}║     🎉 RiskGuard AI Başarıyla Başlatıldı!           ║${NC}"
echo -e "${PURPLE}║                                                       ║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}📡 Servis Bağlantıları:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "🌐 Admin Panel:      ${GREEN}http://localhost:8000${NC}"
echo -e "🔌 API Gateway:      ${GREEN}http://localhost:8000/docs${NC}"
echo -e "🤖 Agent Service:    ${GREEN}http://localhost:8001/docs${NC}"
echo -e "📋 Task Service:     ${GREEN}http://localhost:8002/docs${NC}"
echo -e "💾 Memory Service:   ${GREEN}http://localhost:8003/docs${NC}"
echo -e "🛡️  Risk Service:     ${GREEN}http://localhost:8004/docs${NC}"
echo -e "📧 Email Service:    ${GREEN}http://localhost:8005/docs${NC}"
echo -e "🧠 Ollama API:       ${GREEN}http://localhost:11434${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${YELLOW}📝 Faydalı Komutlar:${NC}"
echo -e "  • Servisleri durdurmak:  ${GREEN}./stop.sh${NC}"
echo -e "  • Logları görüntülemek:  ${GREEN}tail -f /tmp/gateway.log${NC}"
echo -e "  • Servis durumu:         ${GREEN}curl http://localhost:8000/health${NC}"

echo -e "\n${GREEN}✨ Admin paneli tarayıcınızda açılıyor...${NC}\n"

# Tarayıcıda aç (macOS)
sleep 2
open http://localhost:8000 2>/dev/null || echo -e "${YELLOW}Tarayıcınızda http://localhost:8000 adresini açın${NC}"

echo -e "${PURPLE}═══════════════════════════════════════════════════════${NC}\n"
