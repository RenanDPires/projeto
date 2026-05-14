#!/usr/bin/env python3
"""
Script para capturar screenshots do Eletromag Lab para inserir no relatório.
"""

import subprocess
import time
import sys
from pathlib import Path

# Inicia o app em background
print("🚀 Iniciando app Eletromag Lab...")
proc = subprocess.Popen([r".\dist\EEL7216_Lab.exe"], cwd=Path.cwd())

# Aguarda app inicializar
print("⏳ Aguardando inicialização (30s)...")
time.sleep(30)

# Verifica se está rodando
if proc.poll() is None:
    print("✅ App iniciado com sucesso na porta 8501")
    print("🌐 Acesse: http://localhost:8501")
    print("\n📸 Capturas de screenshot podem ser feitas manualmente:")
    print("   - Aba Apresentação")
    print("   - Aba Questão 5 (Cálculo Comparativo)")
    print("   - Aba Questão 5 (Resultados com gráficos)")
    print("\n⏸️  Deixe o app rodando e capture screenshots conforme necessário.")
    print("   Pressione Ctrl+C quando terminar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Encerrando app...")
        proc.terminate()
        proc.wait(timeout=5)
        print("✓ App encerrado")
else:
    print("❌ Falha ao iniciar app")
    sys.exit(1)
