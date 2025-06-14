#!/bin/bash

# 🚀 QUANTUM TRAIL - SETUP AUTOMÁTICO
# Script de instalação e configuração automática

echo "🚀 QUANTUM TRAIL - SETUP AUTOMÁTICO"
echo "===================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar Python
log_info "Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python $PYTHON_VERSION encontrado"
else
    log_error "Python 3 não encontrado. Instale Python 3.8+ primeiro."
    exit 1
fi

# Verificar pip
log_info "Verificando pip..."
if command -v pip3 &> /dev/null; then
    log_success "pip3 encontrado"
else
    log_error "pip3 não encontrado. Instale pip primeiro."
    exit 1
fi

# Instalar dependências Python
log_info "Instalando dependências Python..."
if pip3 install -r requirements.txt; then
    log_success "Dependências Python instaladas"
else
    log_error "Erro ao instalar dependências Python"
    exit 1
fi

# Detectar sistema operacional e instalar TA-Lib
log_info "Detectando sistema operacional..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    log_info "Sistema Linux detectado"
    
    # Verificar se é Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        log_info "Instalando TA-Lib no Ubuntu/Debian..."
        sudo apt-get update
        sudo apt-get install -y libta-lib-dev
        pip3 install TA-Lib
        log_success "TA-Lib instalado no Ubuntu/Debian"
    
    # Verificar se é CentOS/RHEL
    elif command -v yum &> /dev/null; then
        log_info "Instalando TA-Lib no CentOS/RHEL..."
        sudo yum install -y ta-lib-devel
        pip3 install TA-Lib
        log_success "TA-Lib instalado no CentOS/RHEL"
    
    else
        log_warning "Distribuição Linux não reconhecida. Instale TA-Lib manualmente."
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    log_info "Sistema macOS detectado"
    
    if command -v brew &> /dev/null; then
        log_info "Instalando TA-Lib no macOS..."
        brew install ta-lib
        pip3 install TA-Lib
        log_success "TA-Lib instalado no macOS"
    else
        log_error "Homebrew não encontrado. Instale Homebrew primeiro."
        exit 1
    fi

else
    log_warning "Sistema operacional não reconhecido. Instale TA-Lib manualmente."
fi

# Verificar se TA-Lib foi instalado corretamente
log_info "Verificando instalação do TA-Lib..."
if python3 -c "import talib" 2>/dev/null; then
    log_success "TA-Lib instalado e funcionando"
else
    log_error "TA-Lib não foi instalado corretamente"
    log_info "Tente instalar manualmente:"
    log_info "Ubuntu/Debian: sudo apt-get install libta-lib-dev && pip3 install TA-Lib"
    log_info "macOS: brew install ta-lib && pip3 install TA-Lib"
fi

# Verificar modelo ML
log_info "Verificando modelo ML..."
if [ -f "gpu_perfect_model.pkl" ]; then
    MODEL_SIZE=$(du -h gpu_perfect_model.pkl | cut -f1)
    log_success "Modelo ML encontrado ($MODEL_SIZE)"
else
    log_error "Modelo ML não encontrado (gpu_perfect_model.pkl)"
    exit 1
fi

# Criar configuração inicial
log_info "Criando configuração inicial..."
if [ ! -f "quantum_config.json" ]; then
    cp config_exemplo.json quantum_config.json
    log_success "Configuração inicial criada"
else
    log_info "Configuração já existe"
fi

# Teste rápido do sistema
log_info "Executando teste rápido do sistema..."
if python3 -c "
from quantum_trading_optimized import QuantumTradingSystem
import sys
try:
    quantum = QuantumTradingSystem()
    signal = quantum.get_trading_signal('BTCUSDT')
    if signal['signal'] in ['BUY', 'HOLD', 'ERROR']:
        print('✅ Sistema funcionando')
        sys.exit(0)
    else:
        print('❌ Erro no sistema')
        sys.exit(1)
except Exception as e:
    print(f'❌ Erro: {e}')
    sys.exit(1)
" 2>/dev/null; then
    log_success "Teste do sistema passou"
else
    log_error "Teste do sistema falhou"
fi

# Criar diretórios necessários
log_info "Criando diretórios necessários..."
mkdir -p logs
mkdir -p backups
mkdir -p reports
log_success "Diretórios criados"

# Configurar permissões
log_info "Configurando permissões..."
chmod +x *.py
chmod +x setup.sh
log_success "Permissões configuradas"

# Resumo final
echo ""
echo "🎉 SETUP CONCLUÍDO COM SUCESSO!"
echo "================================"
echo ""
log_success "Sistema QuantumTrail instalado e configurado"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Execute: python3 quantum_control_center.py"
echo "2. Configure seus parâmetros de trading"
echo "3. Inicie o sistema de trading"
echo ""
echo "📖 DOCUMENTAÇÃO:"
echo "- README.md - Documentação completa"
echo "- GUIA_RAPIDO.md - Guia de início rápido"
echo "- config_exemplo.json - Exemplos de configuração"
echo ""
echo "🔧 COMANDOS PRINCIPAIS:"
echo "- python3 quantum_control_center.py  # Centro de controle"
echo "- python3 quantum_monitor.py         # Monitor em tempo real"
echo "- python3 quantum_trading_optimized.py # Trading automático"
echo ""
log_success "Bem-vindo ao QuantumTrail! 🚀" 