# Compilação do Executável Autônomo

Este guia descreve como compilar o projeto Eletromag Lab como um executável autônomo que não requer Python instalado.

## Requisitos

- Python 3.12+
- Ambiente virtual criado (`.venv`)
- PyInstaller (será instalado automaticamente)

## Instruções

### Windows

```powershell
# 1. Abra PowerShell na pasta do projeto
cd C:\Users\renan\OneDrive\Área de Trabalho\Renan\UFSC\Mauricio\projeto

# 2. Configure execução de scripts (se necessário)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

# 3. Execute o script de build
.\build_exe.ps1

# Opções:
# .\build_exe.ps1 -Clean     # Remove builds anteriores
# .\build_exe.ps1 -OnlySpec  # Apenas verifica spec
```

### Linux/macOS

```bash
# 1. Abra terminal na pasta do projeto
cd ~/path/to/projeto

# 2. Dê permissão de execução
chmod +x build_exe.sh

# 3. Execute o script de build
./build_exe.sh

# Opção para limpar:
# ./build_exe.sh --clean
```

## Resultado

Após a compilação bem-sucedida:

- **Windows**: `dist\EEL7216_Lab.exe` (executável)
- **Linux/macOS**: `dist/EEL7216_Lab` (executável)

### Tamanho esperado
- ~150-200 MB (inclui Python + todas as dependências)

## Distribuição

O executável é autônomo e pode ser:

1. **Distribuído isoladamente**: Copie apenas o arquivo `.exe` ou executável para outro computador
2. **Compactado**: Crie um arquivo ZIP contendo:
   - `EEL7216_Lab.exe` (ou executável do Linux/macOS)
   - Um arquivo `README.txt` com instruções de uso

## Possíveis Problemas

### "PyInstaller não encontrado"
```powershell
pip install pyinstaller
```

### Erro ao carregar módulos
Verifique se o `.venv` está ativado e todas as dependências estão instaladas:
```powershell
pip install -r requirements.txt
```

### Executável muito lento na primeira execução
Normal! Streamlit extrai e compila recursos na primeira execução. Próximas execuções serão mais rápidas.

### Arquivo grande demais
PyInstaller empacota tudo (Python + libs). Para reduzir tamanho:
1. Remova dependências de desenvolvimento do `requirements.txt`
2. Use UPX para compressão (adicional)

## Troubleshooting

Se o executável não funcionar:

1. Execute no terminal para ver mensagens de erro:
   ```powershell
   .\dist\EEL7216_Lab.exe
   ```

2. Verifique se faltam dependências no `build_exe.spec`:
   ```python
   hiddenimports=[
       # Adicione novos imports aqui
   ]
   ```

3. Recompile com a spec atualizada:
   ```powershell
   .\build_exe.ps1 -Clean
   ```

## Customização

Para modificar o executável:

1. **Nome**: Edite `name="EEL7216_Lab"` em `build_exe.spec`
2. **Ícone**: Adicione `icon="path/to/icon.ico"` em `build_exe.spec`
3. **Modo console**: Altere `console=True` para `console=False` para versão sem console

## Desenvolvimento Contínuo

Durante desenvolvimento, execute normalmente:
```powershell
streamlit run app/main.py
```

Compile apenas quando estiver pronto para distribuição:
```powershell
.\build_exe.ps1
```
