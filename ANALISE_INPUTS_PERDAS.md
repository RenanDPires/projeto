# Análise dos Inputs Necessários para Cálculo de Perdas

## Equação Fundamental de Perdas

$$P = \int\int_{\text{placa}} p(x,y) \, dA$$

onde

$$p(x,y) = \frac{1}{2} \sqrt{\frac{\omega \mu}{2\sigma}} |H(x,y)|^2$$

E o campo magnético (Biot-Savart) é:

$$H(x,y) = \sum_{i=1}^{N} \frac{|I_i|}{2\pi r_i}$$

sendo $r_i$ a distância do i-ésimo condutor ao ponto $(x,y)$.

---

## Inputs Necessários para Obter Perdas da Tabela

### 1. **GEOMETRIA DA PLACA** (FIXA no default)
| Parâmetro | Valor | Unidade |
|-----------|-------|--------|
| Largura | 590 | mm |
| Altura | 270 | mm |
| Espessura | 5.0 | mm |

### 2. **POSIÇÕES E DIÂMETROS DOS FUROS** (FIXA)
| Furo | X (mm) | Y (mm) | Diâmetro (mm) |
|------|--------|--------|---------------|
| 1    | 100.0  | 135.0  | 82.0          |
| 2    | 295.0  | 135.0  | 114.0         |
| 3    | 490.0  | 135.0  | 82.0          |

### 3. **POSIÇÕES DOS CONDUTORES** (FIXA)
| Condutor | X (mm) | Y (mm) |
|----------|--------|--------|
| 1        | 100.0  | 135.0  |
| 2        | 295.0  | 135.0  |
| 3        | 490.0  | 135.0  |

(Coincidentes com os centros dos furos)

### 4. **CORRENTES DOS CONDUTORES** (VARIÁVEL — coluna 1 da tabela)
| Caso | I₁ (A) | I₂ (A) | I₃ (A) |
|------|--------|--------|--------|
| 1    | 2000   | 2000   | 2000   |
| 2    | 2250   | 2250   | 2250   |
| 3    | 2500   | 2500   | 2500   |
| 4    | 2800   | 2800   | 2800   |

**Observação**: Os três condutores carregam a mesma corrente em cada caso.

### 5. **PROPRIEDADES DO MATERIAL** (FIXA)
| Parâmetro | Valor | Unidade | Material |
|-----------|-------|--------|----------|
| μ (permeabilidade) | 1.256637e-6 | H/m | Cobre (não magnético) |
| σ (condutividade) | 5.96e7 | S/m | Cobre |

### 6. **FREQUÊNCIA** (FIXA)
| Parâmetro | Valor | Unidade |
|-----------|-------|--------|
| Frequência | 50 | Hz |
| ω = 2πf | 314.159 | rad/s |

### 7. **DISCRETIZAÇÃO NUMÉRICA** (FIXA)
| Parâmetro | Valor |
|-----------|-------|
| Pontos em X | 50 |
| Pontos em Y | 50 |
| Total | 2500 pontos |

---

## Fluxo de Cálculo

```
INPUTS FIXOS (geometria, material, frequência, malha)
         ↓
         + CORRENTES VARIÁVEIS (2000, 2250, 2500, 2800 A)
         ↓
┌────────────────────────────┐
│ 1. Criar malha 50×50       │
├────────────────────────────┤
│ 2. Calcular H(x,y) via    │
│    Biot-Savart            │
├────────────────────────────┤
│ 3. Calcular p(x,y) de     │
│    H e parâmetros (μ, σ)  │
├────────────────────────────┤
│ 4. Integrar p(x,y) sobre  │
│    região válida (placa   │
│    exceto furos)          │
└────────────────────────────┘
         ↓
    PERDAS (W) — última coluna da tabela
```

---

## Dependência com Corrente

Como $H \propto I$ e $p(x,y) \propto H^2$, temos:

$$P \propto I^2$$

Logo, a razão de perdas entre dois casos é:

$$\frac{P_2}{P_1} = \left(\frac{I_2}{I_1}\right)^2$$

**Verificação com a tabela**:
- Caso 1 → Caso 2: $(2250/2000)^2 = 1.125^2 = 1.2656$ → $60.63 \times 1.2656 ≈ 80.76$ W ✓
- Caso 1 → Caso 3: $(2500/2000)^2 = 1.25^2 = 1.5625$ → $63.79 \times 1.5625 ≈ 99.68$ W ✓
- Caso 1 → Caso 4: $(2800/2000)^2 = 1.4^2 = 1.96$ → $63.79 \times 1.96 ≈ 125.03$ W ✓

---

## Resumo: O que Precisa Variar?

Para reproduzir a tabela de perdas, **apenas as correntes variam**. Tudo mais permanece **constante**:

✓ **Variável**: Correntes (I₁, I₂, I₃)  
✗ **Fixo**: Geometria, Material, Frequência, Malha

Se algum outro parâmetro for alterado (propriedades do material, posição dos condutores, etc.), os resultados mudarão.

