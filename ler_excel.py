import pandas as pd

# Lê o arquivo Excel
df = pd.read_excel('dados/SimulacaoPeloDelta.xlsx')

print("Colunas:", df.columns.tolist())
print("Forma:", df.shape)
print("\nPrimeiras 5 linhas:")
print(df.head())

print("\nÚltimas 5 linhas:")
print(df.tail())

# Gera tabela LaTeX
print("\n" + "="*50)
print("TABELA LATEX:")
print("="*50)

# Cabeçalho da tabela
latex_table = "\\begin{table}[h!]\n"
latex_table += "\\centering\n"
latex_table += "\\caption{Resultados da Simulação por Delta Hedge - Ajuste pelo Delta}\n"
latex_table += "\\label{tab:simulacao-delta}\n"
latex_table += "\\begin{tabular}{|"

# Adiciona colunas baseado no número de colunas do DataFrame
for _ in range(len(df.columns)):
    latex_table += "c|"
latex_table += "}\n"
latex_table += "\\hline\n"

# Cabeçalhos das colunas
headers = []
for col in df.columns:
    # Formata o nome da coluna para LaTeX
    if 'Preço' in col:
        headers.append(col.replace('Preço', 'Preço'))
    elif 'Delta' in col:
        headers.append(col)
    elif 'Diferença' in col:
        headers.append(col.replace('%', '\\%'))
    else:
        headers.append(col)

latex_table += " & ".join(headers) + " \\\\\n"
latex_table += "\\hline\n"

# Dados das linhas (limitando a 10 linhas para não ficar muito grande)
for i, row in df.head(10).iterrows():
    row_data = []
    for col in df.columns:
        value = row[col]
        if pd.isna(value):
            row_data.append("-")
        elif isinstance(value, (int, float)):
            if 'Preço' in col:
                row_data.append(f"R\\$ {value:.2f}")
            elif 'Delta' in col:
                row_data.append(f"{value:.4f}")
            elif 'Diferença' in col:
                row_data.append(f"{value:.2f}\\%")
            else:
                row_data.append(f"{value:.2f}")
        else:
            row_data.append(str(value))
    
    latex_table += " & ".join(row_data) + " \\\\\n"

latex_table += "\\hline\n"
latex_table += "\\end{tabular}\n"
latex_table += "\\end{table}"

print(latex_table) 