# GUIA DE EXECUÇÃO - COMPARAÇÃO DE PREÇOS DE OPÇÕES

## 📋 Resumo dos Programas Disponíveis

### 1️⃣ **ComparadorPrecosOpcoes.py**
- **Localização**: `src/precos/ComparadorPrecosOpcoes.py`
- **Função**: Compara preços de mercado vs Black-Scholes para UMA opção específica
- **Saída**: Tabelas comparativas para os 4 períodos de volatilidade (30, 60, 120, 252 pregões)

### 2️⃣ **GerarResumoComparativo.py**
- **Localização**: `src/precos/GerarResumoComparativo.py`
- **Função**: Gera resumo consolidado para UMA opção
- **Saída**: CSV com estatísticas e insights (`dados-comparacao-preco/resumo_comparativo_simulacao_X.csv`)

### 3️⃣ **AnalisarOpcoes_ITM_ATM_OTM.py**
- **Localização**: `src/precos/AnalisarOpcoes_ITM_ATM_OTM.py`
- **Função**: Analisa as 3 opções (ITM, OTM Borderline, OTM Profundo)
- **Saída**: CSVs individuais + resumo comparativo geral

### 4️⃣ **RelatorioFinal_ITM_ATM_OTM.py**
- **Localização**: `src/precos/RelatorioFinal_ITM_ATM_OTM.py`
- **Função**: Gera relatório consolidado final com insights detalhados
- **Saída**: Relatório formatado + CSV final

---

## 🎯 ORDEM DE EXECUÇÃO RECOMENDADA

### **OPÇÃO A: Análise Rápida de UMA Opção Específica**

Se você quer analisar apenas uma opção específica:

```bash
# 1. Configure o ID da simulação no arquivo
# Edite: src/precos/ComparadorPrecosOpcoes.py
# Linha 13: ID_SIMULACAO = X  (onde X é o ID desejado)

# 2. Execute a comparação
python src/precos/ComparadorPrecosOpcoes.py
```

**IDs de Simulação Disponíveis:**
- `ID_SIMULACAO = 29` → PETRI28 (ITM, Delta 0.82)
- `ID_SIMULACAO = 32` → PETRI333 (OTM Borderline, Delta 0.28)
- `ID_SIMULACAO = 27` → PETRH369 (OTM Profundo, Delta 0.05)

---

### **OPÇÃO B: Análise Completa das 3 Opções (ITM, OTM, OTM Profundo)**

Se você quer analisar todas as 3 opções de uma vez:

```bash
# Execute em ordem:

# 1. Análise individual de cada opção + resumos
python src/precos/AnalisarOpcoes_ITM_ATM_OTM.py

# 2. Relatório consolidado final com insights
python src/precos/RelatorioFinal_ITM_ATM_OTM.py
```

**Arquivos Gerados:**
- `dados-comparacao-preco/resumo_PETRI28.csv`
- `dados-comparacao-preco/resumo_PETRI313.csv`
- `dados-comparacao-preco/resumo_PETRH369.csv`
- `dados-comparacao-preco/resumo_ITM_ATM_OTM.csv`
- `dados-comparacao-preco/relatorio_final_ITM_ATM_OTM.csv`

---

### **OPÇÃO C: Análise Personalizada**

Para criar análises customizadas:

#### Passo 1: Configure a opção desejada
```python
# Edite: src/precos/ComparadorPrecosOpcoes.py
ID_SIMULACAO = 32  # Altere para o ID desejado
```

#### Passo 2: Execute a análise
```bash
python src/precos/ComparadorPrecosOpcoes.py
```

#### Passo 3 (Opcional): Gere resumo estatístico
```python
# Edite: src/precos/GerarResumoComparativo.py
ID_SIMULACAO = 32  # Mesmo ID do passo 1
```

```bash
python src/precos/GerarResumoComparativo.py
```

---

## 📊 ENTENDENDO AS SAÍDAS

### Saída do Terminal

Cada execução mostra:
1. **Cabeçalho com informações da simulação**
   - ID da simulação
   - Período analisado
   - Dados da opção (ticker, strike, vencimento)
   
2. **Para cada período de volatilidade (30, 60, 120, 252 pregões):**
   - Tabela com colunas:
     - Data
     - Dias até Vencimento
     - Preço Ação
     - Preço Mercado
     - Preço BS (Black-Scholes)
     - Delta
     - Diferença %
   
3. **Estatísticas finais:**
   - Total de dias analisados
   - Diferença média entre mercado e BS
   - Melhor período de volatilidade

### Arquivos CSV Gerados

Os CSVs contêm os mesmos dados em formato estruturado para:
- Análise em Excel/Python
- Geração de gráficos
- Documentação do TCC

---

## 🔧 COMO ALTERAR A OPÇÃO ANALISADA

### Para análise de UMA opção:

**Arquivo**: `src/precos/ComparadorPrecosOpcoes.py`

```python
# Linha 13
ID_SIMULACAO = 32  # Altere aqui

# Opções disponíveis:
# 29 - PETRI28 (ITM)
# 32 - PETRI333 (OTM Borderline)
# 27 - PETRH369 (OTM Profundo)
```

### Para análise das 3 opções:

**Arquivo**: `src/precos/AnalisarOpcoes_ITM_ATM_OTM.py` ou `RelatorioFinal_ITM_ATM_OTM.py`

```python
# Linhas 26-45
OPCOES_ANALISAR = [
    {
        'nome': 'PETRI28 (ITM - In The Money)',
        'ticker': 'PETRI28',
        'id_simulacao': 29,  # Altere aqui
        'classificacao': 'ITM'
    },
    # ... demais opções
]
```

---

## 📝 EXEMPLO DE FLUXO COMPLETO

```bash
# 1. Análise completa das 3 opções
python src/precos/RelatorioFinal_ITM_ATM_OTM.py

# Resultado:
# - Análise detalhada de PETRI28 (ITM)
# - Análise detalhada de PETRI333 (OTM Borderline)
# - Análise detalhada de PETRH369 (OTM Profundo)
# - Resumo comparativo final
# - Insights e conclusões

# 2. Verifique os arquivos gerados
ls dados-comparacao-preco/

# Arquivos esperados:
# - resumo_PETRI28.csv
# - resumo_PETRI313.csv
# - resumo_PETRH369.csv
# - relatorio_final_ITM_ATM_OTM.csv
```

---

## ⚙️ PARÂMETROS CONFIGURÁVEIS

Todos os programas usam os mesmos parâmetros padrão:

```python
PREGOES_VOLATILIDADE = [30, 60, 120, 252]  # Períodos testados
TAXA_JUROS = 0.15  # 15% ao ano
```

Para alterar, edite os arquivos correspondentes.

---

## 🎯 RECOMENDAÇÃO PARA O TCC

**Para documentação completa do TCC, execute na ordem:**

```bash
# 1. Relatório consolidado final (mais completo)
python src/precos/RelatorioFinal_ITM_ATM_OTM.py

# 2. (Opcional) Se precisar de dados individuais detalhados
python src/precos/AnalisarOpcoes_ITM_ATM_OTM.py
```

Isso gerará todos os dados e insights necessários para a análise comparativa de preços.

---

## 📌 CLASSIFICAÇÃO DAS OPÇÕES

**Critério baseado no Delta (oficial):**
- **OTM**: Delta 0,00 - 0,30
- **ATM**: Delta 0,31 - 0,70
- **ITM**: Delta 0,71 - 1,00

**Opções analisadas:**
1. **PETRI28**: Delta 0.8163 → **ITM**
2. **PETRI333**: Delta 0.2802 → **OTM Borderline** (próximo a ATM)
3. **PETRH369**: Delta 0.0490 → **OTM Profundo**

---

## ❓ TROUBLESHOOTING

### Erro: "Simulação não encontrada"
- Verifique se o `ID_SIMULACAO` está correto
- IDs válidos: 27, 29, 32

### Erro: "Banco de dados não encontrado"
- Verifique se `banco/mercado_opcoes.db` existe
- Execute do diretório raiz do projeto

### Avisos de deprecação do SQLite
- Avisos normais do Python 3.12
- Não afetam o funcionamento do programa

---

**Última atualização**: Análise configurada para PETRI28, PETRI333 e PETRH369

