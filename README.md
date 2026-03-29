# Eletromag Lab

Laboratorio interativo para simulacoes de eletromagnetismo com foco educacional.

O projeto usa Streamlit para interface e um nucleo numerico em Python para calcular perdas no tanque, campo magnetico e comparacoes entre metodo analitico e Biot-Savart.

## Objetivo

- Permitir simulacao visual e numerica da Questao 1 (perdas no tanque).
- Tornar os calculos transparentes, com comparacao entre metodos.
- Manter arquitetura modular para evolucao de novos exercicios.

## Inicio rapido

### Pre-requisitos

- Python 3.12+
- pip

### Instalacao

```bash
cd projeto

python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

### Executar a aplicacao

```bash
streamlit run app/main.py
```

A interface abre em http://localhost:8501.

## Estrutura do projeto

```text
projeto/
├── app/
│   ├── main.py
│   ├── components/
│   ├── core/
│   │   ├── electromagnetics/
│   │   ├── exercises/
│   │   └── geometry/
│   ├── pages/
│   ├── schemas/
│   └── services/
├── tests/
├── pyproject.toml
├── requirements.txt
├── specs.md
└── README.md
```

## Questao 1: estado atual

### Parametros principais na interface

- Placa: largura, altura e espessura.
- Furos: diametro configuravel no frontend (padrao 82 mm).
- Condutores: corrente global Im e espacamento global a para arranjo de 3 condutores.
- Material: permeabilidade magnetica (mu) e condutividade (sigma), com presets.
- Frequencia de operacao.

### Malha e desempenho

- A malha do calculo principal esta fixa em 1000x1000 na interface da Questao 1.
- Visualizacoes 2D e 3D usam geracao sob demanda para manter a interface responsiva.
- Em graficos de varredura, o numero de pontos pode ser limitado para evitar travamentos.

### Metodos de calculo

- Biot-Savart:
	- Campo magnetico por formulacao vetorial generica.
	- Caso especial analitico para 3 condutores colineares e igualmente espacados.
	- Resultado principal de perdas usando coeficiente normalized.
	- Valor com coeficiente slide19_strict exibido em notas de referencia.
- Metodo analitico:
	- Formula fechada com ln(b/a)=4.347 para referencia comparativa.

### Saidas

- Perda total por metodo analitico (W).
- Perda total por Biot-Savart (W).
- Campo magnetico maximo e densidade de perda maxima.
- Area valida de integracao (placa sem furos).
- Notas de simulacao e comparacao percentual entre metodos.

## Qualidade e testes

Os testes automatizados ficam em tests/ e sao os unicos coletados por padrao via configuracao do pytest.

```bash
python -m pytest --tb=short -q
```

Ultima validacao local: 71 testes passando.

## Desenvolvimento

### Lint e formatacao

```bash
ruff check app tests
black app tests
```

### Type checking

```bash
mypy app tests
```

## Referencias

- Especificacao funcional: specs.md
- Notas tecnicas complementares: IMPLEMENTATION_NOTES.md

## Licenca

MIT
