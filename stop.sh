#!/bin/bash

# RiskGuard AI - Proje Durdurma Scripti
# Tüm servisleri güvenli bir şekilde durdurur

# Renkli çıktı için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║                                                       ║"
echo "║        🛑 RiskGuard AI - Durduruluyor...             ║"
echo "║                                                       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Servisleri port numaralarına göre durdur
echo -e "${YELLOW}🧹 Servisler durduruluyor...${NC}\n"

declare -a ports=(8000 8001 8002 8003 8004 8005)
declare -a names=("Gateway" "Agent" "Task" "Memory" "Risk" "Email")

for i in "${!ports[@]}"; do
    port="${ports[$i]}"
    name="${names[$i]}"

    PID=$(lsof -ti :$port 2>/dev/null)

    if [ ! -z "$PID" ]; then
        kill -9 $PID 2>/dev/null
        echo -e "${GREEN}✅ $name Service durduruldu (Port $port, PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  $name Service zaten çalışmıyor (Port $port)${NC}"
    fi
done

# PID dosyalarını temizle
rm -f /tmp/gateway.pid /tmp/agent-service.pid /tmp/task-service.pid /tmp/memory-service.pid /tmp/risk-service.pid /tmp/email-service.pid 2>/dev/null

echo -e "\n${YELLOW}🤖 Ollama durduruluyor...${NC}"
OLLAMA_PID=$(pgrep -f "ollama serve" 2>/dev/null)
if [ ! -z "$OLLAMA_PID" ]; then
    kill $OLLAMA_PID 2>/dev/null
    echo -e "${GREEN}✅ Ollama durduruldu (PID: $OLLAMA_PID)${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama zaten çalışmıyor${NC}"
fi

echo -e "\n${PURPLE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                       ║${NC}"
echo -e "${PURPLE}║   ✅ Tüm Servisler Başarıyla Durduruldu!            ║${NC}"
echo -e "${PURPLE}║                                                       ║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════════════════╝${NC}\n"
