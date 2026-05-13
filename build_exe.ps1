# Script para compilar o projeto como executável autônomo
# Uso: .\build_exe.ps1

param(
    [switch]$Clean = $false,
    [switch]$OnlySpec = $false
)

$ErrorActionPreference = "Stop"

# Cores para output
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Reset = "`e[0m"

Write-Host "${Green}[INFO]${Reset} Iniciando processo de build do executável..."

# Verificar se o venv está ativado
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "${Red}[ERRO]${Reset} Ambiente virtual (.venv) não encontrado!"
    Write-Host "${Yellow}[DICA]${Reset} Execute: python -m venv .venv"
    exit 1
}

# Ativar venv
Write-Host "${Green}[INFO]${Reset} Ativando ambiente virtual..."
& ".venv\Scripts\Activate.ps1"

# Verificar/instalar PyInstaller
Write-Host "${Green}[INFO]${Reset} Verificando PyInstaller..."
$pyinstaller_check = python -c "import PyInstaller; print('ok')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "${Yellow}[WARN]${Reset} PyInstaller não instalado. Instalando..."
    pip install pyinstaller
}

# Limpar builds anteriores
if ($Clean) {
    Write-Host "${Yellow}[WARN]${Reset} Removendo builds anteriores..."
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "*.spec") { Remove-Item -Force *.spec -ErrorAction SilentlyContinue }
}

# Executar PyInstaller
Write-Host "${Green}[INFO]${Reset} Gerando executável com PyInstaller..."
Write-Host "${Yellow}Spec:${Reset} build_exe.spec"

pyinstaller build_exe.spec --distpath ".\dist" --buildpath ".\build"

if ($LASTEXITCODE -eq 0) {
    $exe_path = ".\dist\EEL7216_Lab.exe"
    if (Test-Path $exe_path) {
        Write-Host "${Green}✓ Sucesso!${Reset}"
        Write-Host "${Green}[INFO]${Reset} Executável criado em: ${Yellow}$exe_path${Reset}"
        Write-Host ""
        Write-Host "${Green}[PRÓXIMOS PASSOS]${Reset}"
        Write-Host "  1. Execute o app: ${Yellow}$exe_path${Reset}"
        Write-Host "  2. Distribua ${Yellow}dist/EEL7216_Lab.exe${Reset} para outros computadores"
        Write-Host ""
        Write-Host "${Yellow}[NOTA]${Reset} Tamanho típico: ~150-200 MB (inclui Python + dependências)"
    }
} else {
    Write-Host "${Red}✗ Erro na compilação!${Reset}"
    exit 1
}
