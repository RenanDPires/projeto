# EEL7216 08202 - Laboratório de Eletromagnética
## Executável Autônomo - Guia de Uso

### ✅ Build Concluído Com Sucesso!

**Data de Compilação:** 2024
**Versão:** 1.0
**Tamanho:** 305.5 MB
**Localização:** `dist/EEL7216_Lab.exe`

---

## 📦 O que está incluído no executável

- **Python 3.12.10** (embutido)
- **Streamlit 1.28.0+** (interface web)
- **Plotly 5.17.0+** (gráficos interativos 2D/3D)
- **NumPy, SciPy** (computação científica)
- **Pydantic** (validação de dados)
- **Todas as dependências do projeto** (Shapely, SymPy, ReportLab, etc.)

---

## 🚀 Como usar

### Opção 1: Clique duplo
1. Navegue até a pasta `dist/`
2. Clique duas vezes em `EEL7216_Lab.exe`
3. Aguarde alguns segundos (primeira execução é mais lenta)
4. Streamlit abrirá no navegador automaticamente

### Opção 2: Terminal/Prompt de Comando
```bash
cd dist
EEL7216_Lab.exe
```

### Opção 3: Distribuição
Para compartilhar com outros usuários:
```bash
# Copiar apenas o executável
xcopy dist\EEL7216_Lab.exe "C:\caminho\destino"

# Ou criar um ZIP
powershell -Command "Compress-Archive -Path dist\EEL7216_Lab.exe -DestinationPath EEL7216_Lab.exe.zip"
```

---

## 📋 Requisitos do Sistema

- **Windows 10/11** (64-bit)
- **Sem necessidade de Python instalado**
- **Sem necessidade de bibliotecas externas**
- **Espaço em disco:** ~350-400 MB (durante execução)
- **RAM:** Mínimo 2GB (recomendado 4GB+)
- **Navegador web:** Chrome, Firefox, Edge, Safari (qualquer um)

---

## 🎯 Funcionalidades Disponíveis

### Apresentação
- Visão geral das 5 questões
- Detalhes técnicos sobre métodos numéricos
- Integração de Gauss-Legendre, Biot-Savart, parametrizações

### Avaliação 1 (5 Questões)
1. **Q1** - Perdas em tanques (análise 3D volumétrica)
2. **Q2** - Soluções analíticas (referência teórica)
3. **Q3** - Biot-Savart (superfícies 3D, cálculo automático)
4. **Q4** - Condutores retangulares (3 variantes)
5. **Q5** - Comparação de métodos (Kaymak et al.)

### Recursos
- Exportação de gráficos em CSV
- Visualização 2D e 3D interativa
- Variação paramétrica (linear/logarítmica)
- Interface responsiva

---

## ⚙️ Configuração de Porta

Por padrão, Streamlit usa a porta `8501`. Se estiver ocupada:

```bash
# Especificar porta diferente (e.g., 8888)
set STREAMLIT_SERVER_PORT=8888
EEL7216_Lab.exe
```

Acesse em: `http://localhost:8888`

---

## 🐛 Resolução de Problemas

### Executável não abre
- Verifique se tem permissão de execução
- Tente executar como administrador (clique direito → "Executar como administrador")
- Verifique antivírus (às vezes bloqueia executáveis desconhecidos)

### Carregamento muito lento na primeira execução
- Streamlit está inicializando (normal)
- Aguarde 20-30 segundos
- Próximas execuções serão mais rápidas

### Erro "Port already in use"
- Feche outras instâncias do navegador ou Streamlit
- Use a opção de porta diferente (veja "Configuração de Porta")

### Gráficos não renderizam
- Verifique conexão com internet (Plotly precisa de CDN na primeira vez)
- Tente atualizar a página (F5)
- Reinicie a aplicação

---

## 📊 Estrutura de Saída

Os gráficos podem ser exportados como CSV através do botão "Exportar" em cada gráfico.

Formato:
```
frequency(Hz), intensity(W/m²), phase(°)
50,          150.3,            45.2
60,          155.1,            44.8
...
```

---

## 🔐 Segurança e Privacidade

- Nenhum dado é transmitido
- Aplicação roda **100% localmente**
- Sem telemetria ou rastreamento
- Sem necessidade de conexão com internet (após primeira execução)

---

## 📝 Sobre o Projeto

**Instituição:** UFSC
**Disciplina:** EEL7216 08202 - Tópicos Especiais em Eletromagnética
**Autor Executável:** GitHub Copilot + PyInstaller
**Data Refatoração:** 2024

---

## 🔗 Arquivos Relacionados

- `BUILD_EXE.md` - Documentação técnica de compilação
- `build_exe_cli.py` - Script Python para recompilar (requer Python)
- `build_exe.spec` - Configuração PyInstaller
- `streamlit_runner.py` - Entry point da aplicação

---

## 📞 Suporte

Para questões sobre funcionalidades:
1. Consulte `README.md` (documentação do projeto)
2. Revise `QUESTAO_*.md` (implementação por questão)
3. Verifique `PROJECT_STATUS_FINAL.txt` (status geral)

---

## ✨ Checklist de Funcionalidade

- ✅ Apresentação com detalhes técnicos
- ✅ Q1 - Análise volumétrica 3D com Gauss-Legendre
- ✅ Q2 - Referência teórica
- ✅ Q3 - Biot-Savart com superfícies 3D automáticas
- ✅ Q4 - Três variantes de condutores retangulares
- ✅ Q5 - Comparação Kaymak/Chen/Liu/Belarbi
- ✅ Exportação CSV em todos os gráficos
- ✅ Navegação via sidebar
- ✅ Rebranding para código da disciplina
- ✅ Interface responsiva
- ✅ Sem dependências externas

---

**Pronto para usar! Divirta-se explorando! 🚀**
