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

## Deploy no Cloudflare Workers

O app principal continua sendo Streamlit/Python e, por isso, não roda diretamente no runtime de Workers.
Para publicação simples via GitHub + Cloudflare, o repositório agora inclui um scaffold estático em
`cloudflare/` com `wrangler.toml`, worker de fallback e uma landing page para deploy.

### Fluxo de deploy

1. Crie um Worker no Cloudflare e gere um `CLOUDFLARE_API_TOKEN` com permissão de deploy.
2. Salve `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_API_TOKEN` como secrets do repositório no GitHub.
3. Faça push para `main`.
4. O workflow em `.github/workflows/deploy-cloudflare-workers.yml` publica o conteúdo estático de `cloudflare/public`.

### Limitação importante

Esse deploy entrega uma vitrine estática do projeto. Se a intenção for rodar a interface Streamlit completa no edge, será preciso uma reescrita da UI e da camada de cálculo para uma stack compatível com Workers.

## Referencias

- Especificacao funcional: specs.md
- Notas tecnicas complementares: IMPLEMENTATION_NOTES.md

## Licenca

MIT
