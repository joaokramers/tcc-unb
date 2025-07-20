import pandas as pd

# Lê o arquivo Excel
df = pd.read_excel('dados/MelhorCenario.xlsx')

print("Colunas:", df.columns.tolist())
print("Forma:", df.shape)
print("\nPrimeiras 5 linhas:")
print(df.head().to_string())

print("\nÚltimas 5 linhas:")
print(df.tail().to_string())

# Gera tabela LaTeX
print("\n" + "="*50)
print("TABELA LATEX - MELHOR CENÁRIO:")
print("="*50)

# Cabeçalho da tabela
latex_table = "\\begin{table}[h!]\n"
latex_table += "\\centering\n"
latex_table += "\\small\n"
latex_table += "\\caption{Comparação dos Melhores Cenários por Estratégia de Delta Hedge}\n"
latex_table += "\\label{tab:melhor-cenario}\n"
latex_table += "\\begin{tabular}{|c|c|c|c|c|c|c|}\n"
latex_table += "\\hline\n"

# Cabeçalhos das colunas
headers = ["Opção", "Strike", "Período", "Estratégia", "Parâmetros", "Ajustes", "Saldo Final"]
latex_table += "\\textbf{" + "} & \\textbf{".join(headers) + "} \\\\\n"
latex_table += "& \\textbf{(R\\$)} & & \\textbf{Ótima} & \\textbf{Ótimos} & \\textbf{(\\#)} & \\textbf{(R\\$)} \\\\\n"
latex_table += "\\hline\n"

# Dados das linhas
for i, row in df.iterrows():
    # Extrai dados específicos
    opcao = row['Opção']
    strike = row['Strike']
    inicio = str(row['Início'])
    termino = str(row['Término'])
    ajuste = row['Ajuste']
    valor = row['Valor']
    pregoes_vol = row['Pregões Volatilidade']
    num_ajustes = row['# Ajustes']
    saldo_final = row['Saldo Final']
    
    # Formata período (pega só dia e mês)
    try:
        ini_fmt = pd.to_datetime(inicio).strftime('%d/%m')
        ter_fmt = pd.to_datetime(termino).strftime('%d/%m')
        periodo = f"{ini_fmt}-{ter_fmt}"
    except:
        periodo = f"{inicio}-{termino}"
    
    # Formata estratégia e parâmetros
    estrategia_str = str(ajuste) if pd.notna(ajuste) else "-"
    
    # Formata parâmetros baseado no tipo de ajuste
    if pd.notna(valor) and pd.notna(pregoes_vol):
        if ajuste == 'Delta':
            parametros_str = f"Δ={valor:.2f}/{pregoes_vol:.0f}"
        elif ajuste == 'Dias':
            parametros_str = f"Freq={valor:.0f}/{pregoes_vol:.0f}"
        elif ajuste == 'Lote':
            parametros_str = f"Lote={valor:.0f}/{pregoes_vol:.0f}"
        else:
            parametros_str = f"{valor:.2f}/{pregoes_vol:.0f}"
    else:
        parametros_str = "-"
    
    # Formata valores
    strike_str = f"{strike}" if isinstance(strike, str) else f"{strike:.2f}"
    ajustes_str = f"{num_ajustes:.0f}" if pd.notna(num_ajustes) else "-"
    saldo_str = f"{saldo_final}" if isinstance(saldo_final, str) else f"{saldo_final:.2f}"
    
    latex_table += f"{opcao} & {strike_str} & {periodo} & {estrategia_str} & {parametros_str} & {ajustes_str} & {saldo_str} \\\\\n"

latex_table += "\\hline\n"
latex_table += "\\end{tabular}\n"
latex_table += "\\end{table}"

print(latex_table) 