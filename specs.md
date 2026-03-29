# Eletromag Lab — Especificação Funcional e Técnica

## 1. Visão geral

O Eletromag Lab é um ambiente interativo em Python para estudo de problemas de eletromagnetismo com foco em visualização, rastreabilidade dos cálculos e comparação entre métodos.

O escopo implementado atualmente está concentrado na Questão 1: perdas no tanque devido a condutores carregados atravessando furos em uma placa.

## 2. Estado atual validado

Antes da atualização desta especificação, o estado do projeto foi validado com execução da suíte automatizada.

- Resultado: 71 testes aprovados.
- Coleta de testes: somente a pasta tests, conforme pyproject.

## 3. Objetivos do produto

- Didático: facilitar interpretação física com gráficos, fórmulas e métricas.
- Interativo: permitir ajuste de parâmetros e recálculo sob demanda.
- Modular: separar UI, validação geométrica e núcleo numérico.
- Reprodutível: manter entradas estruturadas e saídas serializáveis.

## 4. Arquitetura atual

### 4.1 Camadas

- Interface: Streamlit em app/main.py.
- Domínio e cálculo: app/core.
- Modelos de entrada e saída: app/schemas.
- Validação e testes: tests.

### 4.2 Organização do repositório

```text
projeto/
├─ app/
│  ├─ main.py
│  ├─ components/
│  ├─ core/
│  │  ├─ electromagnetics/
│  │  ├─ exercises/
│  │  └─ geometry/
│  ├─ pages/
│  ├─ schemas/
│  └─ services/
├─ tests/
├─ pyproject.toml
├─ requirements.txt
├─ specs.md
└─ README.md
```

## 5. Escopo funcional da Questão 1

### 5.1 Entradas da interface

- Placa: largura, altura e espessura em mm.
- Furos: diâmetro global em mm, com posições conforme configuração ativa.
- Condutores: correntes por condutor e opção de corrente global Im.
- Espaçamento em x: parâmetro global a para arranjo com 3 furos e 3 condutores.
- Material: permeabilidade magnética mu e condutividade sigma.
- Frequência de operação em Hz.

### 5.2 Discretização

- A malha da simulação principal está fixa em 1000 x 1000 no frontend da Questão 1.
- Visualizações paramétricas usam malha reduzida para manter responsividade.

### 5.3 Saídas

- Perda total pelo método analítico.
- Perda total pelo método Biot-Savart.
- Diferença percentual entre métodos.
- Campo magnético máximo, densidade de perda máxima e área válida.
- Notas textuais com parâmetros de cálculo e referência do modo estrito.

## 6. Modelo matemático implementado

### 6.1 Campo magnético

O cálculo de campo usa duas estratégias no núcleo:

- Caso geral: superposição vetorial por Biot-Savart para correntes de linha.
- Caso especial de 3 condutores: expressão analítica fechada quando condições geométricas e de corrente são atendidas.

### 6.2 Perdas

As perdas por Biot-Savart são integradas numericamente com máscara geométrica:

$$
P = k \iint |H_m(x,y)|^2\, dA
$$

com $k$ dependente de $\omega$, $\mu$ e $\sigma$.

Também é calculado o método analítico com formulação fechada de referência, incluindo o termo geométrico $\ln(b/a)=4.347$.

## 7. Regras geométricas e validação

O sistema valida e sinaliza, entre outros:

- furo fora da placa;
- sobreposição de furos;
- condutor fora da placa;
- espessura ou dimensões inválidas;
- inconsistências de material.

A máscara de integração inclui apenas a região da placa fora dos furos.

## 8. Interface e comportamento

### 8.1 Fluxo de uso

1. Usuário altera parâmetros na tela da Questão 1.
2. Sistema valida entradas geométricas e físicas.
3. Cálculo é executado ao clicar em Calcular.
4. Resultados são exibidos com comparação de métodos.
5. Exportação disponível em JSON e CSV.

### 8.2 Visualizações

- Geometria da placa, furos e condutores.
- Curvas 2D de perdas por corrente, espessura e frequência.
- Superfícies 3D comparativas em subplots lado a lado entre analítico e Biot-Savart.
- Geração de gráficos 2D e 3D sob demanda para controle de desempenho.

## 9. Testes e qualidade

### 9.1 Escopo de testes automatizados

- Geometria e validações.
- Modelos Pydantic.
- Integração da Questão 1.
- Consistência com dados de referência e critério de erro do comparativo Biot-Savart vs analítico.

### 9.2 Ferramentas

- Pytest
- Ruff
- Black
- Mypy

## 10. Requisitos não funcionais

- Manutenibilidade: separação entre interface e núcleo numérico.
- Confiabilidade: validação de entradas e testes automatizados.
- Desempenho: controle de custo computacional com geração sob demanda nas visualizações.
- Clareza: documentação e comentários em português.

## 11. Backlog técnico sugerido

- Consolidar scripts exploratórios em uma pasta dedicada fora da raiz.
- Expandir validações para cenários adicionais de múltiplos condutores.
- Criar suíte específica para visualizações e exportação.
- Preparar interface para novos exercícios mantendo o mesmo contrato de dados.

## 12. Resumo executivo

O projeto está funcional para a Questão 1, com comparação entre método analítico e Biot-Savart, malha principal fixa em 1000 x 1000, visualizações 2D e 3D sob demanda e suíte de testes aprovada. A base está pronta para evolução incremental de novos exercícios.
