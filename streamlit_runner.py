#!/usr/bin/env python3
"""
Entry point para execução autônoma do Streamlit como executável.
Este script inicia a aplicação Streamlit de forma programática.
"""

import sys
import os
from pathlib import Path

# Garante que o diretório raiz do projeto está no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importa e executa o Streamlit
import streamlit.web.cli as cli


def main():
    """Inicia a aplicação Streamlit."""
    app_path = str(PROJECT_ROOT / "app" / "main.py")
    
    # Define argumentos para o Streamlit
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.port=8501",
        "--logger.level=warning",
        "--client.showErrorDetails=true",
        "--client.toolbarMode=minimal",
    ]
    
    # Executa o Streamlit
    cli.main()


if __name__ == "__main__":
    main()
