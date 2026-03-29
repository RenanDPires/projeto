# Eletromag Lab — Especificação Funcional e Técnica

## 1. Visão geral

**Objetivo do projeto:** construir um ambiente interativo, com front-end e back-end em Python, para resolver exercícios de eletromagnetismo de forma visual, permitindo:

- editar dimensões geométricas pela interface;
- aplicar modelos matemáticos e físicos a partir dos parâmetros de entrada;
- visualizar geometria, campos e resultados numéricos;
- evoluir o sistema para múltiplos tipos de exercícios.

O sistema deve funcionar como um **laboratório visual de eletromagnetismo**, onde cada exercício é tratado como um módulo independente, reutilizando uma base comum de geometria, discretização, cálculo e visualização.

---

## 2. Escopo inicial

O escopo inicial contempla a **Questão 1** do recorte apresentado:

### Tema
**Perdas no tanque devido aos condutores carregados**.

### Ideia central
O usuário deverá editar a geometria da tampa/placa do tanque e os parâmetros físicos do problema. O sistema calculará o campo magnético sobre a região da placa e estimará as perdas por integração numérica.

### O sistema deve permitir

- definir as dimensões da placa;
- definir a espessura da placa;
- definir quantidade, posição e diâmetro dos furos;
- definir posição dos condutores;
- definir parâmetros elétricos e de material;
- calcular o campo magnético em uma malha 2D;
- calcular perdas totais e distribuição espacial de perdas;
- exibir resultados visualmente.

---

## 3. Objetivos do produto

1. **Didático:** facilitar a compreensão visual de problemas de eletromagnetismo.
2. **Interativo:** permitir alteração imediata dos parâmetros geométricos e físicos.
3. **Modular:** suportar novos exercícios no futuro sem reescrever a base.
4. **Reprodutível:** garantir que os cálculos sejam consistentes e auditáveis.
5. **Expansível:** possibilitar futura separação entre front-end e API.

---

## 4. Arquitetura proposta

## 4.1 Estratégia de implementação

Será adotada uma arquitetura em duas camadas lógicas:

- **Front-end em Python** para interação, entrada de parâmetros e visualização.
- **Back-end em Python** para regras de negócio, cálculo numérico e organização dos exercícios.

### Recomendação para MVP
Para a primeira versão, pode-se usar:

- **Streamlit** como front-end interativo;
- **módulos Python internos** como back-end local;
- posterior evolução para **FastAPI** se houver necessidade de API separada.

### Alternativa futura
- **FastAPI** no back-end;
- **Streamlit** ou **Dash** no front-end;
- comunicação HTTP entre interface e motor de cálculo.

---

## 4.2 Stack sugerida

### Front-end
- Python 3.11+
- Streamlit
- Plotly

### Back-end / motor numérico
- Python 3.11+
- NumPy
- SciPy
- SymPy (opcional para apoio simbólico)
- Shapely (opcional para manipulação geométrica)

### Qualidade e organização
- Pydantic para validação de dados
- Pytest para testes
- Ruff para lint
- Black para formatação
- Mypy opcional para tipagem estática

---

## 5. Organização do repositório

```text
project_root/
├─ app/
│  ├─ main.py                    # ponto de entrada do front-end
│  ├─ pages/
│  │  └─ exercise_01.py          # página da Questão 1
│  ├─ components/
│  │  ├─ inputs.py               # componentes de entrada
│  │  ├─ plots.py                # gráficos e mapas
│  │  └─ tables.py               # tabelas de saída
│  ├─ core/
│  │  ├─ geometry/
│  │  │  ├─ plate.py             # placa, furos e validações geométricas
│  │  │  └─ mesh.py              # geração de malha
│  │  ├─ electromagnetics/
│  │  │  ├─ biot_savart.py       # campo magnético
│  │  │  ├─ losses.py            # cálculo das perdas
│  │  │  └─ units.py             # conversões de unidade
│  │  └─ exercises/
│  │     └─ q01_tank_losses.py   # orquestração do exercício 1
│  ├─ schemas/
│  │  ├─ inputs.py               # modelos de entrada
│  │  └─ outputs.py              # modelos de saída
│  └─ services/
│     └─ simulation.py           # serviço de simulação
│
├─ tests/
│  ├─ test_geometry.py
│  ├─ test_field.py
│  ├─ test_losses.py
│  └─ test_q01.py
│
├─ requirements.txt
├─ pyproject.toml
├─ README.md
└─ specs.md
```

---

## 6. Conceitos do domínio

## 6.1 Entidades principais

### Placa
Representa a tampa ou chapa onde as perdas serão calculadas.

Atributos esperados:
- largura;
- altura;
- espessura;
- material;
- sistema de referência geométrica.

### Furo
Representa a passagem de um condutor pela placa.

Atributos esperados:
- centro `(x, y)`;
- diâmetro ou raio.

### Condutor
Representa o elemento percorrido por corrente.

Atributos esperados:
- posição `(x, y)` no corte;
- corrente;
- fase ou sinal, se aplicável;
- orientação geométrica simplificada.

### Material
Representa as propriedades da placa.

Atributos esperados:
- permeabilidade magnética `μ`;
- condutividade elétrica `σ`.

### Simulação
Representa uma execução completa do exercício.

Atributos esperados:
- parâmetros geométricos;
- parâmetros físicos;
- malha utilizada;
- campo calculado;
- perdas calculadas;
- metadados da execução.

---

## 7. Escopo funcional da Questão 1

## 7.1 Entradas editáveis na interface

### Geometria da placa
- largura da placa [mm]
- altura da placa [mm]
- espessura da placa [mm]

### Geometria dos furos
- quantidade de furos
- posição dos centros [mm]
- diâmetro de cada furo [mm]

### Condutores
- quantidade de condutores
- posição dos condutores [mm]
- corrente por condutor [A]

### Propriedades físicas
- frequência [Hz]
- permeabilidade `μ`
- condutividade `σ`

### Discretização numérica
- resolução da malha em `x`
- resolução da malha em `y`
- estratégia de refinamento opcional

---

## 7.2 Saídas esperadas

### Numéricas
- valor total da perda `P`
- valor máximo local de `|H(x, y)|`
- valor máximo local de densidade de perda
- área efetiva de integração

### Visuais
- desenho da placa com os furos;
- posição dos condutores;
- mapa de calor de `|H(x, y)|`;
- mapa de calor da densidade de perdas;
- cortes 1D em linhas selecionáveis;
- tabela resumo dos parâmetros.

### Textuais
- equações utilizadas;
- observações sobre aproximações adotadas;
- mensagens de validação geométrica.

---

## 8. Modelo matemático inicial

## 8.1 Campo magnético

O sistema deve permitir implementar o cálculo de campo magnético sobre a superfície da placa, com base na formulação adotada no exercício.

A primeira implementação poderá usar uma expressão analítica já definida para `H_m(x, y)` ou uma composição por condutores idealizados.

Forma geral esperada:

```math
H_m(x,y) = f(I, x, y, a, ...)
```

A equação específica usada na Questão 1 deve ser encapsulada em um módulo próprio, para que possa ser substituída futuramente sem afetar a interface.

---

## 8.2 Perdas

A formulação apresentada no recorte indica uma perda total do tipo:

```math
P = \frac{1}{2}\sqrt{\frac{\omega \mu}{2\sigma}} \iint |H_m(x,y)|^2 \, dx \, dy
```

onde:

- `ω = 2πf`
- `μ` é a permeabilidade
- `σ` é a condutividade
- `H_m(x,y)` é o campo magnético na placa

### Requisitos de implementação
- a integral deve ser resolvida numericamente sobre a região válida da placa;
- a região interna dos furos deve ser excluída da integração;
- o resultado deve ser consistente com as unidades do SI.

---

## 9. Requisitos geométricos

## 9.1 Sistema de coordenadas

Adotar um sistema cartesiano 2D para o plano da placa:

- origem preferencial no canto inferior esquerdo, ou no centro da placa;
- a convenção escolhida deve ser única em todo o projeto.

### Recomendação
Usar origem no **canto inferior esquerdo** para facilitar edição via interface.

---

## 9.2 Regras de validação

O sistema deve impedir ou sinalizar:

- furo fora da placa;
- condutor fora da área útil;
- sobreposição indevida entre furos;
- diâmetros negativos ou nulos;
- espessura negativa ou nula;
- malha com resolução inválida.

---

## 9.3 Máscara geométrica

A placa deverá ser representada por:

- um domínio retangular;
- menos os domínios circulares internos dos furos.

Essa máscara será usada para:
- desenhar a geometria;
- limitar a malha válida;
- excluir regiões da integral.

---

## 10. Estratégia numérica

## 10.1 Malha

Gerar uma malha regular 2D em toda a placa.

### Parâmetros mínimos
- `nx`: número de pontos em x
- `ny`: número de pontos em y

### Requisito
Todos os pontos devem ser classificados como:
- válidos para cálculo;
- inválidos por pertencerem ao exterior ou ao interior de furos.

---

## 10.2 Integração

A integração numérica pode ser feita inicialmente por:

- soma ponderada em malha regular;
- com `dx * dy` constante.

Futuras melhorias possíveis:
- integração adaptativa;
- refinamento local próximo aos condutores.

---

## 10.3 Desempenho

O MVP não exige otimização extrema, mas deve responder de forma fluida para malhas usuais.

### Meta de experiência
- recalcular em até poucos segundos para casos padrão;
- permitir ajuste de resolução para balancear precisão e desempenho.

---

## 11. Requisitos de interface

## 11.1 Organização da tela

A tela da Questão 1 deve conter pelo menos quatro áreas:

### A. Painel de parâmetros
Entradas geométricas, físicas e numéricas.

### B. Visualização da geometria
Desenho da placa, furos e condutores.

### C. Visualização do campo/perdas
Heatmaps e gráficos de corte.

### D. Resultados numéricos
Valor de perdas, estatísticas e observações.

---

## 11.2 Comportamento esperado

- qualquer alteração de parâmetro deve permitir recalcular a solução;
- valores inválidos devem ser sinalizados claramente;
- fórmulas podem ser mostradas com LaTeX;
- a interface deve deixar claro quais unidades estão sendo usadas.

---

## 11.3 Recursos desejáveis

- botão “Restaurar exemplo padrão”;
- botão “Recalcular”;
- exportação de imagem;
- exportação de parâmetros e resultados em JSON ou CSV.

---

## 12. Modelos de dados sugeridos

## 12.1 Entradas

```python
from pydantic import BaseModel, Field
from typing import List

class HoleInput(BaseModel):
    x_mm: float
    y_mm: float
    diameter_mm: float

class ConductorInput(BaseModel):
    x_mm: float
    y_mm: float
    current_a: float

class MaterialInput(BaseModel):
    mu: float
    sigma: float

class MeshInput(BaseModel):
    nx: int = Field(ge=10)
    ny: int = Field(ge=10)

class PlateInput(BaseModel):
    width_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    thickness_mm: float = Field(gt=0)

class Exercise01Input(BaseModel):
    plate: PlateInput
    holes: List[HoleInput]
    conductors: List[ConductorInput]
    material: MaterialInput
    frequency_hz: float = Field(gt=0)
    mesh: MeshInput
```

---

## 12.2 Saídas

```python
class Exercise01Result(BaseModel):
    total_loss_w: float
    max_h_field: float
    max_loss_density: float
    valid_area_m2: float
    notes: list[str]
```

Observação: matrizes grandes (`x_grid`, `y_grid`, `h_field`, `loss_density`, `mask`) podem permanecer em estruturas NumPy no motor interno e serem convertidas apenas quando necessário para visualização.

---

## 13. API futura (opcional)

Caso o projeto evolua para separação front/back, a API mínima sugerida é:

### `POST /api/v1/exercises/q01/simulate`
Recebe os parâmetros da Questão 1 e retorna o resultado da simulação.

### `GET /api/v1/exercises`
Lista exercícios disponíveis.

### `GET /api/v1/exercises/q01/defaults`
Retorna valores padrão.

### `POST /api/v1/exercises/q01/validate`
Valida os dados sem executar a simulação completa.

---

## 14. Fluxo da simulação da Questão 1

1. Ler parâmetros da interface.
2. Validar dimensões, furos e condutores.
3. Converter unidades para SI.
4. Gerar malha 2D.
5. Construir máscara geométrica da placa.
6. Calcular `H_m(x, y)` na malha válida.
7. Calcular densidade local proporcional a `|H_m(x, y)|^2`.
8. Integrar numericamente a região válida.
9. Gerar saídas numéricas e visuais.
10. Atualizar a interface.

---

## 15. Critérios de aceitação do MVP

O MVP será considerado funcional quando:

1. a interface permitir editar dimensões da placa e dos furos;
2. a geometria for redesenhada após alteração dos parâmetros;
3. o cálculo do campo for executado na malha;
4. a integral de perdas for computada;
5. o valor total de perda for exibido ao usuário;
6. pelo menos um heatmap for exibido corretamente;
7. regiões de furos não forem integradas;
8. entradas inválidas gerarem mensagens claras.

---

## 16. Requisitos não funcionais

### Manutenibilidade
- módulos pequenos e bem nomeados;
- baixo acoplamento entre UI, geometria e solver.

### Legibilidade
- código comentado apenas onde necessário;
- funções com responsabilidade única.

### Reusabilidade
- o solver da Questão 1 não deve depender diretamente de componentes da interface.

### Testabilidade
- cálculos devem ser testáveis sem executar o front-end.

---

## 17. Estratégia de testes

## 17.1 Testes unitários

### Geometria
- ponto dentro/fora da placa;
- ponto dentro/fora de furo;
- validação de furo fora do domínio.

### Campo
- consistência dimensional;
- comportamento esperado em pontos de teste;
- ausência de falhas numéricas em posições válidas.

### Perdas
- integral em caso simplificado conhecido;
- exclusão correta dos furos;
- sensibilidade à resolução da malha.

---

## 17.2 Testes de integração

- entrada completa da Questão 1 gera resposta sem erro;
- alteração de um parâmetro altera o resultado;
- exportações funcionam corretamente, se implementadas.

---

## 18. Roadmap sugerido

## Fase 1 — Base do projeto
- estruturar repositório;
- configurar ambiente Python;
- criar modelos Pydantic;
- criar página inicial.

## Fase 2 — Geometria
- desenhar placa;
- adicionar furos;
- validar domínio;
- gerar malha.

## Fase 3 — Solver da Questão 1
- implementar `H_m(x, y)`;
- implementar integral numérica;
- calcular perda total.

## Fase 4 — Visualização
- heatmap do campo;
- heatmap das perdas;
- gráficos de corte.

## Fase 5 — Robustez
- testes automatizados;
- presets de exercícios;
- exportação de resultados.

## Fase 6 — Expansão
- adicionar novos exercícios;
- extrair API com FastAPI;
- salvar simulações.

---

## 19. Riscos e decisões técnicas

## Riscos
- ambiguidades na formulação física de cada exercício;
- singularidades ou instabilidades numéricas próximas aos condutores;
- aumento de complexidade ao tentar generalizar cedo demais.

## Decisões recomendadas
- começar com um exercício fechado e bem definido;
- manter unidades internas no SI;
- desacoplar interface e solver desde o início;
- documentar aproximações físicas adotadas em cada exercício.

---

## 20. Convenções de implementação

### Unidades
- interface: preferencialmente mm, A, Hz;
- motor interno: SI (m, A, s, S/m, H/m etc.).

### Idioma do código
- nomes de arquivos e identificadores em inglês;
- textos de interface podem ficar em português.

### Estilo
- funções curtas;
- classes focadas em dados ou comportamento bem delimitado;
- evitar lógica numérica dentro dos componentes de UI.

---

## 21. Definição de pronto da Questão 1

A Questão 1 estará pronta quando houver:

- edição visual dos parâmetros principais;
- desenho geométrico consistente da placa e dos furos;
- cálculo de campo funcional;
- cálculo de perdas funcional;
- exibição clara dos resultados;
- testes básicos cobrindo geometria e integração.

---

## 22. Diretriz para uso com Copilot

Este projeto deve ser desenvolvido em pequenos incrementos. Ao usar o Copilot, priorizar prompts e tarefas na seguinte ordem:

1. criar estrutura de pastas e arquivos-base;
2. implementar modelos de entrada e validação;
3. implementar geometria da placa e dos furos;
4. implementar geração de malha;
5. implementar solver de campo;
6. implementar cálculo de perdas;
7. conectar solver à interface;
8. adicionar testes unitários;
9. refinar visualizações.

### Regras para geração assistida de código
- não misturar UI com cálculo numérico;
- toda função numérica deve ter docstring curta;
- toda entrada do usuário deve ser validada;
- sempre converter unidades explicitamente;
- todo novo módulo deve vir acompanhado de pelo menos um teste.

---

## 23. Primeiro backlog técnico

### BL-001
Criar estrutura inicial do projeto com Streamlit.

### BL-002
Implementar modelos Pydantic de entrada da Questão 1.

### BL-003
Implementar desenho 2D da placa e dos furos.

### BL-004
Implementar validação geométrica.

### BL-005
Implementar geração de malha regular 2D.

### BL-006
Implementar cálculo de `H_m(x, y)`.

### BL-007
Implementar cálculo de perdas por integração numérica.

### BL-008
Implementar heatmap do campo magnético.

### BL-009
Implementar heatmap da densidade de perdas.

### BL-010
Criar testes unitários mínimos para geometria e perdas.

---

## 24. Resumo executivo

O projeto será um ambiente visual e modular para resolução de exercícios de eletromagnetismo em Python. A primeira entrega focará no problema de perdas em uma placa/tampa de tanque com condutores carregados passando por furos. O sistema deverá permitir edição geométrica pela interface, cálculo numérico do campo magnético, integração das perdas e visualização gráfica dos resultados.

A prioridade é construir uma base limpa e reutilizável, capaz de receber novos exercícios no futuro.
