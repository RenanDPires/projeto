# Eletromag Lab

**Ambiente interativo e modular para resolução visual de exercícios de eletromagnetismo.**

Um laboratório educacional desenvolvido em Python, combinando front-end interativo (Streamlit) e motor numérico robusto, para permitir que estudantes explorem problemas de eletromagnetismo através de simulações visuais e editáveis.

## 🎯 Objetivo

Construir uma ferramenta educacional para:

- Editar **geometria** (dimensões, furos, condutores) pela interface
- Aplicar **modelos matemáticos e físicos** aos parâmetros de entrada
- **Visualizar** geometria, campos e resultados numéricos em tempo real
- Evoluir o sistema para **múltiplos exercícios** de forma modular

## 🚀 Início rápido

### Pré-requisitos

- Python 3.13+
- pip ou uv

### Instalação

```bash
# Clone or navigate to the project
cd projeto

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development (includes pytest, ruff, black, mypy):
pip install -r requirements.txt
pip install -e ".[dev]"
```

### Executar a aplicação

```bash
streamlit run app/main.py
```

A aplicação abrir-se-á em `http://localhost:8501`.

## 📁 Estrutura do Projeto

```
projeto/
├── app/
│   ├── main.py                    # Entrada principal (Streamlit)
│   ├── pages/                     # Páginas da aplicação
│   ├── components/                # Componentes de UI
│   ├── core/
│   │   ├── geometry/              # Geometria e malhas
│   │   ├── electromagnetics/       # Cálculos EM e perdas
│   │   └── exercises/             # Orquestração de exercícios
│   ├── schemas/                   # Validação (Pydantic)
│   └── services/                  # Lógica de serviço
├── tests/                         # Testes automatizados
├── pyproject.toml                 # Configuração de build
├── requirements.txt               # Dependências
├── specs.md                       # Especificação funcional completa
└── README.md
```

## 📋 Fase 1 — MVP da Questão 1

### Questão 1: Perdas no tanque devido aos condutores carregados

A primeira fase implementa o cálculo de perdas magnéticas em uma placa com furos por onde passam condutores carregados.

#### Entradas editáveis
- Dimensões da placa (largura, altura, espessura)
- Furos (quantidade, posição, diâmetro)
- Condutores (posição, corrente)
- Propriedades do material (μ, σ)
- Frequência, resolução da malha

#### Saídas esperadas
- Valor total de perda [W]
- Distribuição espacial de perdas (heatmap)
- Campo magnético na placa (heatmap)
- Estatísticas numéricas

## 🔧 Desenvolvimento

### Executar testes

```bash
pytest tests/
pytest tests/ -v --cov=app  # Com cobertura
```

### Verificar qualidade de código

```bash
# Lint
ruff check app/ tests/

# Formatação
black app/ tests/

# Type checking
mypy app/ tests/
```

### Formatar código automaticamente

```bash
black app/ tests/
ruff check --fix app/ tests/
```

## 📚 Referências

- **Especificação completa**: veja [specs.md](specs.md)
- **Seção 14**: Fluxo da simulação
- **Seção 22**: Diretriz para uso com Copilot
- **Seção 23**: Primeiro backlog técnico

## 📝 Stack

### Front-end
- **Streamlit**: Interface interativa
- **Plotly**: Gráficos e heatmaps

### Backend / Numérico
- **NumPy**: Operações matriciais
- **SciPy**: Integração numérica, funções especiais
- **Pydantic**: Validação de dados
- **Shapely**: Manipulação geométrica (futuro)
- **SymPy**: Suporte simbólico (futuro)

### QA & Tooling
- **Pytest**: Testes automatizados
- **Ruff**: Linting
- **Black**: Formatação
- **Mypy**: Type checking

## 📜 Licença

MIT

## 👤 Autores

- **Renan** — desenvolvimento inicial

---

**Status**: Fase 1 em desenvolvimento (BL-001 e BL-002 em progresso)
