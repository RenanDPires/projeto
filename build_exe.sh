#!/bin/bash
# Script para compilar o projeto como executável autônomo (Linux/macOS)
# Uso: chmod +x build_exe.sh && ./build_exe.sh

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} Iniciando processo de build do executável..."

# Verificar se o venv existe
if [ ! -f ".venv/bin/activate" ]; then
    echo -e "${RED}[ERRO]${NC} Ambiente virtual (.venv) não encontrado!"
    echo -e "${YELLOW}[DICA]${NC} Execute: python3 -m venv .venv"
    exit 1
fi

# Ativar venv
echo -e "${GREEN}[INFO]${NC} Ativando ambiente virtual..."
source .venv/bin/activate

# Verificar/instalar PyInstaller
echo -e "${GREEN}[INFO]${NC} Verificando PyInstaller..."
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}[WARN]${NC} PyInstaller não instalado. Instalando..."
    pip install pyinstaller
fi

# Limpar builds anteriores (opcional)
if [ "$1" = "--clean" ]; then
    echo -e "${YELLOW}[WARN]${NC} Removendo builds anteriores..."
    rm -rf dist build *.spec || true
fi

# Executar PyInstaller
echo -e "${GREEN}[INFO]${NC} Gerando executável com PyInstaller..."
echo -e "${YELLOW}Spec:${NC} build_exe.spec"

pyinstaller build_exe.spec --distpath "./dist" --buildpath "./build"

if [ $? -eq 0 ]; then
    EXE_PATH="./dist/EEL7216_Lab"
    if [ -f "$EXE_PATH" ]; then
        echo -e "${GREEN}✓ Sucesso!${NC}"
        echo -e "${GREEN}[INFO]${NC} Executável criado em: ${YELLOW}$EXE_PATH${NC}"
        echo ""
        echo -e "${GREEN}[PRÓXIMOS PASSOS]${NC}"
        echo -e "  1. Execute o app: ${YELLOW}$EXE_PATH${NC}"
        echo -e "  2. Distribua ${YELLOW}dist/EEL7216_Lab${NC} para outros computadores"
        echo ""
        echo -e "${YELLOW}[NOTA]${NC} Tamanho típico: ~150-200 MB (inclui Python + dependências)"
    fi
else
    echo -e "${RED}✗ Erro na compilação!${NC}"
    exit 1
fi
