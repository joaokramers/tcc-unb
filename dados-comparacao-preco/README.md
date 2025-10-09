# Dados de Comparação de Preços - Black-Scholes vs Mercado

Esta pasta contém os resultados da análise comparativa entre preços de mercado e preços teóricos calculados pelo modelo Black-Scholes para opções de compra (calls) da Petrobras.

## 📊 Opções Analisadas

### Classificação por Delta (Critério Oficial)
- **Delta 0,00-0,30**: OTM (Out of The Money)
- **Delta 0,31-0,70**: ATM (At The Money)
- **Delta 0,71-1,00**: ITM (In The Money)

### Opções Selecionadas

| Opção | Delta | Classificação | Strike | Vencimento | ID Simulação |
|-------|-------|---------------|--------|------------|--------------|
| PETRI28 | 0.8163 | ITM | R$ 28.22 | 2025-09-19 | 29 |
| PETRI313 | 0.6518 | ATM | R$ 29.22 | 2025-09-19 | 31 |
| PETRH369 | 0.0490 | OTM | R$ 36.23 | 2025-08-15 | 27 |

## 📁 Arquivos Gerados

### Arquivos Individuais por Opção
- **`resumo_PETRI28.csv`**: Análise da opção ITM para os 4 períodos de volatilidade (30, 60, 120, 252 pregões)
- **`resumo_PETRI313.csv`**: Análise da opção ATM para os 4 períodos de volatilidade
- **`resumo_PETRH369.csv`**: Análise da opção OTM para os 4 períodos de volatilidade

### Arquivos Consolidados
- **`resumo_ITM_ATM_OTM.csv`**: Comparação geral das 3 opções com melhores períodos
- **`relatorio_final_ITM_ATM_OTM.csv`**: Relatório final consolidado com todas as métricas

### Arquivos de Simulações Específicas
- **`resumo_comparativo_simulacao_XX.csv`**: Resumos gerados para simulações específicas (quando executado individualmente)

## 🔬 Períodos de Volatilidade Analisados

Cada opção foi analisada com 4 diferentes períodos históricos para cálculo da volatilidade:

| Pregões | Período Aproximado | Descrição |
|---------|-------------------|-----------|
| 30 | ~6 semanas | Volatilidade de curto prazo |
| 60 | ~3 meses | Volatilidade de médio prazo |
| 120 | ~6 meses | Volatilidade de médio-longo prazo |
| 252 | ~1 ano | Volatilidade anualizada |

## 📈 Métricas Calculadas

Para cada combinação de opção e período de volatilidade:

- **Volatilidade**: Volatilidade histórica anualizada calculada
- **Diferença Média**: Diferença percentual média entre preço de mercado e Black-Scholes
- **Diferença Mínima**: Menor diferença observada no período
- **Diferença Máxima**: Maior diferença observada no período
- **Desvio Padrão**: Dispersão das diferenças percentuais
- **Dias Analisados**: Quantidade de dias úteis no período da simulação

## 🎯 Principais Descobertas

### PETRI28 (ITM)
- **Melhor período**: 30 pregões (volatilidade curta)
- **Diferença média**: -23.32%
- **Conclusão**: Mercado precifica consistentemente abaixo do modelo BS

### PETRI313 (ATM)
- **Melhor período**: 252 pregões (volatilidade anual)
- **Diferença média**: +0.30%
- **Conclusão**: Excelente aderência ao modelo BS - mercado mais eficiente

### PETRH369 (OTM)
- **Melhor período**: 120 pregões
- **Diferença média**: Extrema (valores astronômicos)
- **Conclusão**: Limitação do modelo BS para opções profundamente OTM

## 🔧 Parâmetros Utilizados

- **Taxa de juros**: 15% ao ano (0.15)
- **Dias úteis por ano**: 252
- **Tipo de opção**: Call (opção de compra)
- **Ativo subjacente**: PETR4

## 📚 Como os Dados Foram Gerados

Os dados foram gerados pelos seguintes programas:

1. **`src/precos/ComparadorPrecosOpcoes.py`**: Análise individual de uma opção
2. **`src/precos/AnalisarOpcoes_ITM_ATM_OTM.py`**: Análise das 3 opções simultaneamente
3. **`src/precos/RelatorioFinal_ITM_ATM_OTM.py`**: Relatório consolidado final
4. **`src/precos/GerarResumoComparativo.py`**: Resumo para uma simulação específica

## 📊 Estrutura dos Arquivos CSV

### Resumos Individuais (`resumo_PETRIXX.csv`)
```
Pregões Vol. | Volatilidade | Diferença Média | Diferença Mín. | Diferença Máx. | Desvio Padrão | Dias
```

### Resumo Consolidado (`resumo_ITM_ATM_OTM.csv`)
```
Opção | Classificação | Strike | Melhor Período | Diferença Média
```

### Relatório Final (`relatorio_final_ITM_ATM_OTM.csv`)
```
Opção | Classificação | Strike | Moneyness | Melhor Período | Volatilidade | Diferença Média
```

## 📖 Interpretação dos Resultados

### Diferença Positiva (+)
- Preço de mercado **ACIMA** do preço teórico Black-Scholes
- Opção pode estar "cara" segundo o modelo

### Diferença Negativa (-)
- Preço de mercado **ABAIXO** do preço teórico Black-Scholes
- Opção pode estar "barata" segundo o modelo

### Diferença Próxima a Zero
- Alta aderência entre mercado e modelo teórico
- Indicativo de mercado eficiente naquela faixa de preço

## ⚠️ Observações Importantes

1. **Opções OTM profundas**: Apresentam diferenças percentuais extremas devido a divisão por valores próximos a zero
2. **Volatilidade**: Impacta significativamente os preços teóricos calculados
3. **Período ótimo**: Varia conforme a classificação da opção (ITM, ATM, OTM)
4. **Limitações do BS**: O modelo tem limitações conhecidas para opções muito OTM próximas ao vencimento

---

**Data da última atualização**: Outubro de 2025  
**Fonte dos dados**: Banco de dados `banco/mercado_opcoes.db`  
**Projeto**: TCC - Análise de Estratégias de Delta Hedge

