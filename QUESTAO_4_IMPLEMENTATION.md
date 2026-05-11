# Questão 4 - Condutores Retangulares de Cobre

## Sumário Executivo

Questão 4 foi **TOTALMENTE IMPLEMENTADA** com:
- **(a) Deduções analíticas** das três variantes de geometria usando referências Del Vecchio (2010) e Kulkarni (2013)
- **(b) Cálculo numérico** da densidade superficial de perdas [W/m²] com dados fornecidos
- **Interface Streamlit** com 3 abas: Derivações | Cálculo Numérico | Figura 3
- **18 testes unitários** validando todas as equações e comportamentos

**Status: ✅ COMPLETO** (104/104 testes passando)

---

## Figura 3: Três Variantes de Condutores Retangulares de Cobre

```
┌───────────────────────────────────────────────────────────────────────────┐
│                  VARIANTE (a): Campo em Ambas as Superfícies             │
│                                                                           │
│   Geometria:           Condição de Contorno:                            │
│                                                                           │
│    y                  H_z(±b) = H₀  (simetria)                          │
│    ↑                  H_z(0) = H₀·cosh(b/δ)                             │
│    │    H₀     H₀     H_z(x) = H₀·cosh(x/δ)                             │
│  ──┼─ → [▓▓▓▓▓▓] ← ──                                                    │
│    │    -b  0  b      Solução: cosh(x/δ)                                │
│    └─→  x                                                                │
│                                                                           │
│   Fórmula de Perdas:  P_a = (H₀²/σδ)·tanh(b/δ)                          │
│   Máx J_r:           J_max = σωμ₀H₀·sinh(b/δ)                          │
│   Aplicação:         Condutor imerso em campo uniforme                  │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│              VARIANTE (b): Campo em Uma Superfície (Semi-espaço)         │
│                                                                           │
│   Geometria:           Condição de Contorno:                            │
│                                                                           │
│                       H_z(y=0) = H₀  (superfície)                       │
│                       H_z(y→∞) = 0    (profundidade)                    │
│    y                  H_z(y) = H₀·exp(-y/δ)                             │
│    ↑  H₀ ┌─ − − − ─ ┐                                                    │
│    │  ────>[▓▓▓▓▓▓▓▓] Condutor (semi-espaço)                            │
│  y=0 ┌─ − − − ─ ┐  │                                                    │
│    │ │          │  │                                                    │
│    │ │  δ (3δ)  │  │                                                    │
│    └─┴──────────┘→ x                                                    │
│                                                                           │
│   Fórmula de Perdas:  P_b = H₀²/(σδ)                 [CASO BASE]        │
│   Máx J_r:           J_max = σωμ₀H₀  (em y=0)                          │
│   Aplicação:         Condutor em placa laminar                          │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│            VARIANTE (c): Espaço Finito (Sanduíche Laminado)             │
│                                                                           │
│   Geometria:           Condição de Contorno:                            │
│                                                                           │
│    y                  H_z(x=0) = H₀   (superfície esquerda)            │
│    ↑                  H_z(x=b) = 0    (superfície direita)             │
│  y=b H₀ ┌─────────┐                                                    │
│    │ ───┤[▓▓▓▓▓▓]├─ Condutor (espaço finito)                           │
│  y=0    └─────────┘  H_z(x)=H₀·sinh((b-x)/δ)/sinh(b/δ)               │
│           ←  b  →    x                                                 │
│                                                                           │
│   Fórmula de Perdas:  P_c = (H₀²/σδ)·coth(b/δ) = (H₀²/σδ)·1/tanh(b/δ) │
│   Máx J_r:           J_max = σωμ₀H₀·[1/tanh(b/δ)]                     │
│   Aplicação:         Sanduíche com confinamento bidimensional           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Dados da Questão 4

| Parâmetro | Símbolo | Valor | Unidade |
|-----------|---------|-------|---------|
| Campo magnético superficial | H₀ | 6.0 | A/m |
| Condutividade (cobre) | σ | 5.8×10⁷ | S/m |
| Meia-largura do condutor | b | 2.5 | cm |
| Largura total | 2b | 5.0 | cm |
| Frequência | f | 60 | Hz |
| Permeabilidade relativa | μᵣ | 1.0 | — (cobre não-magnético) |

---

## Resultados Numéricos

### Parâmetros Derivados

| Parâmetro | Valor | Unidade |
|-----------|-------|---------|
| Frequência angular ω | 376.99 | rad/s |
| Profundidade de penetração δ | 8.5316 | mm |
| Razão adimensional b/δ | 2.9303 | — |
| Fator tanh(b/δ) | 0.99432 | — |
| Fator coth(b/δ) = 1/tanh | 1.00571 | — |

### Densidade Superficial de Perdas [W/m²]

| Variante | Fórmula | Perdas (W/m²) | Relativo a (b) |
|----------|---------|---------------|---|
| **(a)** | H₀²/(σδ) · tanh(b/δ) | **7.2338×10⁻⁵** | **0.9943** |
| **(b)** | H₀²/(σδ) | **7.2752×10⁻⁵** | **1.0000** |
| **(c)** | H₀²/(σδ) · coth(b/δ) | **7.3168×10⁻⁵** | **1.0057** |

**Interpretação**: 
- Variante (a) tem ~0.57% **menos** perdas que (b)
- Variante (c) tem ~0.57% **mais** perdas que (b)
- A simetria de tanh e coth reflete-se nas perdas: P_a < P_b < P_c

### Densidade de Corrente Induzida Máxima [A/m²]

| Variante | J_max | Localização |
|----------|-------|------------|
| (a) | 1.5398×10⁶ | Em x = ±b (superfícies) |
| (b) | 1.6486×10⁵ | Em y = 0 (superfície) |
| (c) | 1.6580×10⁵ | Em x = 0 (centro) |

---

## Equações Fundamentais

### Profundidade de Penetração (Skin Effect)

$$\delta = \sqrt{\frac{2}{\omega\mu\sigma}} = \sqrt{\frac{2}{2\pi f \mu_0 \sigma}}$$

Para cobre a 60 Hz com σ = 5.8×10⁷ S/m:
$$\delta = 8.53 \text{ mm}$$

### Equação de Difusão em Coordenadas Cartesianas

$$\frac{\partial^2 H_z}{\partial x^2} - \frac{\omega\mu\sigma}{2}(1-j) H_z = 0$$

Solução: ondas evanescentes com comprimento de atenuação δ

### Variante (a) - Ambas as Superfícies

**Condição de contorno**: $H_z(±b) = H_0$, geometria simétrica

**Solução**: 
$$H_z(x) = H_0 \cosh\left(\frac{x}{\delta}\right)$$

**Densidade de corrente**:
$$J_x(x) = \sigma \omega \mu_0 H_0 \sinh\left(\frac{x}{\delta}\right)$$

**Perdas por unidade de área**:
$$P_a = \int_{-b}^{b} \frac{|J_x|^2}{\sigma} dx = \frac{H_0^2}{\sigma\delta} \tanh\left(\frac{b}{\delta}\right)$$

### Variante (b) - Uma Superfície (Semi-espaço)

**Condição de contorno**: $H_z(0) = H_0$, $H_z(\infty) = 0$

**Solução**:
$$H_z(y) = H_0 \exp\left(-\frac{y}{\delta}\right)$$

**Perdas por unidade de área**:
$$P_b = \int_0^{\infty} \frac{|J_x|^2}{\sigma} dy = \frac{H_0^2}{\sigma\delta}$$

### Variante (c) - Espaço Finito (Sanduíche)

**Condição de contorno**: $H_z(0) = H_0$, $H_z(b) = 0$

**Solução**:
$$H_z(x) = H_0 \frac{\sinh\left(\frac{b-x}{\delta}\right)}{\sinh\left(\frac{b}{\delta}\right)}$$

**Perdas por unidade de área**:
$$P_c = \frac{H_0^2}{\sigma\delta} \coth\left(\frac{b}{\delta}\right) = \frac{H_0^2}{\sigma\delta} \frac{1}{\tanh(b/\delta)}$$

---

## Implementação em Código

### Módulo Principal: `q04_rectangular_conductors.py`

Função: `solve_question_04_rectangular_conductors(...)`

**Entrada**:
- `half_width_b_cm`: Meia-largura b [cm]
- `surface_magnetic_field_h0_a_per_m`: Campo H₀ [A/m]
- `conductivity_s_per_m`: Condutividade σ [S/m]
- `frequency_hz`: Frequência f [Hz]
- `permeability_rel`: Permeabilidade relativa μᵣ (padrão: 1.0)

**Saída**: `Q4RectangularConductor(BaseModel)` com:
- Parâmetros geométricos e operacionais
- Skin depth δ e razão b/δ
- Perdas P_a, P_b, P_c [W/m²]
- Densidades de corrente máximas J_max [A/m²]
- Razões comparativas P_a/P_b, P_c/P_b
- Notas físicas

### Visualizações: `rectangular_conductors.py`

Funções:
- `create_q4_geometry_figure()` - Exibe os 3 perfis de H_z(x) e H_z(y)
- `create_q4_power_loss_comparison()` - Tabela comparativa de perdas

---

## Referências Utilizadas

### Del Vecchio (2010)
**Transformer Design Principles** - 2ª edição
- Seção 15.3.2.1 "Eddy Current Losses in the Coils" (página 426)
- Coeficientes hiperbólicos para geometria retangular
- Relação entre frequência e profundidade de penetração

### Kulkarni & Khaparde (2013)
**Transformer Engineering: Design, Technology, and Diagnostics**
- Seção 4.5.1 "Expression for the eddy loss" (página 150)
- Fórmulas alternativas para validação cruzada
- Aplicações práticas em transformadores

---

## Interface Streamlit

**Localização**: `app/main.py` - Função `_show_assessment_q4_tab()`

**Estrutura de 3 Abas**:

1. **Parte (a): Deduções**
   - Equações em LaTeX para as 3 variantes
   - Geometrias e condições de contorno
   - Fórmulas de perdas

2. **Parte (b): Cálculo Numérico**
   - Entrada interativa: b, σ, f, H₀
   - Cálculo automático de δ, P_a, P_b, P_c
   - Tabela comparativa com razões
   - Densidade de corrente máxima
   - Notas físicas

3. **Figura 3: Geometrias**
   - Visualização dos perfis H_z(x) para cada variante
   - Tabela de comparação de perdas com gráficos Plotly
   - Apresentação das estruturas físicas

---

## Testes Unitários

**Arquivo**: `tests/test_q04_rectangular.py` - **18 testes**

**Cobertura**:
1. **TestQ4ParameterDerivation** (3 testes)
   - Cálculo correto de δ
   - Verificação de ω = 2πf
   - Dependência de frequência: δ ∝ 1/√f

2. **TestVariantACalculations** (3 testes)
   - Intervalo de tanh: 0 < tanh < 1
   - Positividade de perdas
   - Dependência quadrática: P ∝ H₀²

3. **TestVariantBCalculations** (2 testes)
   - Positividade de perdas
   - Verificação de intervalo físico

4. **TestVariantCCalculations** (2 testes)
   - Intervalo de coth: coth > 1
   - Positividade de perdas

5. **TestComparativeBehavior** (3 testes)
   - Relação fundamental: tanh·coth = 1
   - Consistência de razões P_a/P_b, P_c/P_b
   - Variante (b) como caso base

6. **TestCurrentDensity** (2 testes)
   - Positividade de J_max
   - Intervalo físico: 10³-10⁸ A/m²

7. **TestModelConsistency** (3 testes)
   - Tipos de saída corretos
   - Consistência de parâmetros geométricos
   - Reprodutibilidade com dados da questão

**Status**: ✅ 18/18 testes **PASSANDO**

---

## Status Geral

| Componente | Status | Detalhes |
|-----------|--------|----------|
| Módulo analítico | ✅ | `q04_rectangular_conductors.py` |
| Geometrias & gráficos | ✅ | `rectangular_conductors.py` |
| Interface Streamlit | ✅ | 3 abas com entrada interativa |
| Testes unitários | ✅ | 18/18 passando |
| Referências | ✅ | Del Vecchio + Kulkarni |
| Suite completa | ✅ | 104/104 testes (Q1+Q2+Q4 + anteriores) |

---

## Próximas Etapas

1. **Q5**: Comparação de métodos para resistência AC e indutância de fuga
2. **Otimização**: Possível refatoração de UI para melhor consistência
3. **Documentação**: Documentos técnicos finais com derivações completas
4. **Validação**: Comparação com resultados publicados e dados de laboratório

---

## Resumo dos Arquivos Criados/Modificados

```
✅ app/core/electromagnetics/rectangular_conductors.py (NOVO)
   └─ Visualizações das geometrias e tabelas comparativas

✅ app/core/exercises/q04_rectangular_conductors.py (NOVO)
   └─ Solução analítica das 3 variantes

✅ app/main.py (MODIFICADO)
   └─ Adicionada função _show_assessment_q4_tab() com 3 abas

✅ tests/test_q04_rectangular.py (NOVO)
   └─ 18 testes unitários de Q4

📊 Resultados:
   └─ 104/104 testes passando (18 Q4 + 86 anteriores)
```

---

**Data**: Maio 2026
**Versão**: Q4 v1.0 - Completo
