#!/usr/bin/env python3
"""
Script cross-platform para compilar o projeto Eletromag Lab como executável.
Funciona em Windows, Linux e macOS.

Uso:
  python build_exe_cli.py                 # Build padrão
  python build_exe_cli.py --clean         # Remove builds anteriores
  python build_exe_cli.py --help          # Mostra ajuda
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path


class Colors:
    """ANSI colors for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_info(msg: str):
    print(f"{Colors.GREEN}[INFO]{Colors.RESET} {msg}")


def print_warn(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}[ERRO]{Colors.RESET} {msg}")


def print_success(msg: str):
    print(f"{Colors.GREEN}{Colors.BOLD}✓ {msg}{Colors.RESET}")


def print_section(msg: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{msg:^60}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.RESET}\n")


def get_venv_python() -> Path | None:
    """Retorna o executável Python do .venv, se existir."""
    venv_path = Path(".venv")
    if not venv_path.exists():
        return None

    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"

    if python_path.exists():
        return python_path.resolve()
    return None


def check_pyinstaller(python_exec: Path):
    """Verifica se PyInstaller está instalado no interpretador informado."""
    try:
        result = subprocess.run(
            [str(python_exec), "-c", "import PyInstaller; print(PyInstaller.__version__)"],
            check=True,
            capture_output=True,
            text=True,
        )
        print_info(f"PyInstaller encontrado: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print_warn("PyInstaller não instalado")
        return False


def check_venv():
    """Verifica se o venv existe e está ativado."""
    venv_path = Path(".venv")
    if venv_path.exists():
        print_info(f"Ambiente virtual encontrado: {venv_path.resolve()}")
        return True
    else:
        print_error(f"Ambiente virtual não encontrado: {venv_path}")
        return False


def check_runtime_dependencies(python_exec: Path):
    """Valida se dependências críticas existem no mesmo ambiente do build."""
    print_info("Validando dependências críticas (streamlit, plotly, numpy, scipy)...")
    check_code = (
        "import streamlit, plotly, numpy, scipy; "
        "print('OK:', streamlit.__version__, plotly.__version__)"
    )
    try:
        result = subprocess.run(
            [str(python_exec), "-c", check_code],
            check=True,
            capture_output=True,
            text=True,
        )
        print_info(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        if stderr:
            print_error(stderr)
        print_error("Dependências críticas ausentes no ambiente usado para build")
        return False


def clean_builds():
    """Remove builds anteriores."""
    print_section("Limpando Builds Anteriores")
    
    paths_to_remove = [
        Path("dist"),
        Path("build"),
        Path(".pyinstaller"),
    ]
    
    for path in paths_to_remove:
        if path.exists():
            print_info(f"Removendo {path}...")
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink()
    
    # Mantém arquivos .spec versionados do projeto.
    
    print_success("Build limpo!")


def build_executable(python_exec: Path):
    """Executa PyInstaller para compilar o executável."""
    print_section("Compilando Executável")
    
    spec_file = "build_exe.spec"
    
    if not Path(spec_file).exists():
        print_error(f"Arquivo {spec_file} não encontrado!")
        print_info(f"Execute este script no diretório raiz do projeto")
        return False
    
    print_info(f"Usando spec: {spec_file}")
    
    cmd = [
        str(python_exec),
        "-m", "PyInstaller",
        spec_file,
        "--distpath", "./dist",
        "--workpath", "./build",
    ]
    
    print_info(f"Executando: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print_success("Compilação concluída!")
            return True
        else:
            print_error("Compilação falhou!")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao executar PyInstaller: {e}")
        return False
    except FileNotFoundError:
        print_error("PyInstaller não encontrado no PATH")
        print_info("Execute: pip install pyinstaller")
        return False


def verify_output():
    """Verifica se o executável foi criado com sucesso."""
    print_section("Verificando Resultado")
    
    dist_path = Path("dist")
    
    if not dist_path.exists():
        print_error("Diretório dist não encontrado!")
        return False
    
    # Procura pelo executável
    exe_patterns = ["EEL7216_Lab*", "EEL7216_Lab.exe"]
    executables = []
    
    for pattern in exe_patterns:
        executables.extend(dist_path.glob(pattern))
    
    if executables:
        exe = executables[0]
        size_mb = exe.stat().st_size / (1024 * 1024)
        
        print_success(f"Executável criado com sucesso!")
        print(f"\n  Localização: {Colors.BOLD}{exe.resolve()}{Colors.RESET}")
        print(f"  Tamanho: {size_mb:.1f} MB")
        print(f"\n  Diretório dist: {Colors.BOLD}{dist_path.resolve()}{Colors.RESET}")
        
        return True
    else:
        print_error("Executável não encontrado em dist/")
        print_info(f"Conteúdo de dist/: {list(dist_path.iterdir())}")
        return False


def print_next_steps():
    """Exibe próximos passos."""
    print_section("Próximos Passos")
    
    exe_name = "EEL7216_Lab.exe" if sys.platform == "win32" else "EEL7216_Lab"
    
    print(f"""
{Colors.BOLD}1. Testar o executável:{Colors.RESET}
   cd dist
   ./{exe_name}

{Colors.BOLD}2. Distribuir:{Colors.RESET}
   Copie dist/{exe_name} para qualquer computador (não requer Python)

{Colors.BOLD}3. Empacotar para distribuição:{Colors.RESET}
   Crie um ZIP: dist/ → {exe_name}.zip
   Adicione um README.txt com instruções

{Colors.BOLD}Tamanho típico:{Colors.RESET}
   ~150-200 MB (inclui Python + todas as dependências)

{Colors.BOLD}Documentação completa:{Colors.RESET}
   Veja BUILD_EXE.md
    """)


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Compilar Eletromag Lab como executável autônomo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python build_exe_cli.py              # Build padrão
  python build_exe_cli.py --clean      # Limpa builds anteriores
  python build_exe_cli.py --no-check   # Pula verificações
        """
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove builds anteriores antes de compilar"
    )
    
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Pula verificações pré-compilação"
    )
    
    args = parser.parse_args()
    
    print_section("Eletromag Lab - Compilador de Executável")
    
    venv_python = get_venv_python()
    if venv_python is None:
        print_error("Python do .venv não encontrado")
        print_info("Crie/ative o venv do projeto antes de compilar")
        return 1

    print_info(f"Usando Python do venv: {venv_python}")

    # Verificações pré-compilação
    if not args.no_check:
        print_section("Verificações Pré-Compilação")
        
        if not check_venv():
            print_error("Ambiente virtual não configurado!")
            print_info("Execute: python -m venv .venv")
            return 1
        
        if not check_pyinstaller(venv_python):
            print_warn("Instalando PyInstaller...")
            try:
                subprocess.run(
                    [str(venv_python), "-m", "pip", "install", "pyinstaller"],
                    check=True
                )
                print_success("PyInstaller instalado!")
            except subprocess.CalledProcessError:
                print_error("Falha ao instalar PyInstaller")
                return 1

        if not check_runtime_dependencies(venv_python):
            return 1
    
    # Limpar builds se solicitado
    if args.clean:
        clean_builds()
    
    # Compilar
    if not build_executable(venv_python):
        print_error("Falha na compilação!")
        return 1
    
    # Verificar resultado
    if not verify_output():
        print_error("Executável não foi criado!")
        return 1
    
    # Próximos passos
    print_next_steps()
    
    print_success("Build concluído com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
