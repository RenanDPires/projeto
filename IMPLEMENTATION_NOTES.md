# Notas de Implementação — Perdas Eletromagnéticas

## 1. Objetivo deste documento

Registrar as decisões técnicas e a implementação atual do cálculo de perdas da Questão 1, com base nas notas da Aula 02 do Prof. Mauricio, sem uso de fatores empíricos de calibração ad hoc.

## 2. Referência teórica

Documento base:

- Aula_02_Prof_Mauricio_EEL7216_Perdas_Regioes_Condutoras.pdf

Pontos utilizados:

- Slides 16 a 18: formulação analítica para perdas.
- Slide 19: formulação com Biot-Savart para 3 condutores.
- Slide 20: gabarito de referência para validação.

## 3. Métodos implementados

### 3.1 Método analítico

O método analítico é calculado por expressão fechada com termo geométrico fixo:

$$
P = \left(\frac{I_m^2 q}{\pi \sigma}\right) \ln\left(\frac{b}{a}\right)
\left[\frac{\sinh(qc)-\sin(qc)}{\cosh(qc)+\cos(qc)}\right]
$$

onde:

- $q = \sqrt{\omega\mu\sigma/2}$
- $\omega = 2\pi f$
- $\ln(b/a)=4.347$

Implementação no núcleo eletromagnético:

- cálculo analítico de perdas disponível no módulo de eletromagnetismo;
- uso como referência direta na comparação de métodos.

### 3.2 Método Biot-Savart

O método Biot-Savart é aplicado de duas formas:

- expressão fechada para 3 condutores colineares, igualmente espaçados e com mesma magnitude de corrente;
- formulação vetorial genérica por superposição para casos fora da condição especial.

As perdas são integradas na área válida da placa (descontando furos), usando máscara geométrica e discretização regular.

## 4. Coeficientes de perdas

O cálculo numérico de perdas no método Biot-Savart utiliza:

- modo normalized como resultado principal;
- modo slide19_strict calculado e reportado como referência adicional nas notas da simulação.

Essa separação preserva comparabilidade com o fluxo atual do aplicativo e com os testes existentes.

## 5. Geometria e discretização

- Placa e furos são tratados no plano 2D com unidades internas em SI.
- A máscara geométrica inclui somente pontos válidos para integração.
- Na interface da Questão 1, a malha principal está fixa em 1000 x 1000.
- Para visualizações 2D e 3D, são usadas malhas reduzidas e geração sob demanda, evitando sobrecarga de renderização.

## 6. Parâmetros operacionais atuais

Valores usuais de validação na Questão 1:

- placa de referência: 590 x 270 x 5 mm;
- três furos com diâmetro padrão de 82 mm;
- frequência típica de validação: 60 Hz;
- material de referência: mu = 1.256637e-4 H/m, sigma = 1.0e6 S/m.

## 7. Qualidade e validação

Validação executada antes desta atualização de documentação:

- suíte de testes automatizados: 71 aprovados;
- verificação de consistência entre método analítico e Biot-Savart em cenário de referência;
- manutenção do critério de erro físico definido nos testes dedicados.

## 8. Decisões relevantes

- Remoção de fator de calibração empírico legado.
- Separação explícita de responsabilidades entre cálculo de campo, perdas por Biot-Savart e perdas analíticas.
- Documentação e comentários priorizados em português para consistência do projeto.

## 9. Limitações conhecidas

- O caso especial fechado de 3 condutores depende de condições geométricas e de corrente específicas.
- Visualizações paramétricas densas podem ter custo alto; por isso há limitação de pontos e execução sob demanda.

## 10. Próximas melhorias sugeridas

- Consolidar scripts exploratórios em pasta dedicada para reduzir ruído na raiz.
- Criar testes adicionais de regressão para visualizações e exportação.
- Expandir validação para geometrias mais gerais de condutores.
