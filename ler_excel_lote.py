import pandas as pd

# Lê o arquivo Excel
df = pd.read_excel('dados/SimulacaoPeloLote.xlsx')

print("Colunas:", df.columns.tolist())
print("Forma:", df.shape)
print("\nPrimeiras 3 linhas:")
print(df.head(3).to_string())

print("\nÚltimas 3 linhas:")
print(df.tail(3).to_string())

# Gera tabela LaTeX
print("\n" + "="*50)
print("TABELA LATEX - AJUSTE PELO LOTE:")
print("="*50)

# Cabeçalho da tabela
latex_table = "\\begin{table}[h!]\n"
latex_table += "\\centering\n"
latex_table += "\\small\n"
latex_table += "\\caption{Resultados da Simulação de Delta Hedge - Ajuste por Lote}\n"
latex_table += "\\label{tab:simulacao-lote}\n"
latex_table += "\\begin{tabular}{|c|c|c|c|c|c|c|}\n"
latex_table += "\\hline\n"

# Cabeçalhos das colunas
headers = ["Opção", "Strike", "Período", "Delta", "Parâmetros", "Ajustes", "Saldo Final"]
latex_table += "\\textbf{" + "} & \\textbf{".join(headers) + "} \\\\\n"
latex_table += "& \\textbf{(R\\$)} & & \\textbf{Ini→Fin} & \\textbf{Lote/VOL} & \\textbf{(\\#)} & \\textbf{(R\\$)} \\\\\n"
latex_table += "\\hline\n"

# Dados das linhas
for i, row in df.iterrows():
    # Extrai dados específicos
    opcao = row['Opção']
    strike = row['Strike']
    inicio = str(row['Início'])
    termino = str(row['Término'])
    delta_ini = row['D.Inicial']
    delta_fin = row['D.Final']
    limite_lote = row['Limite Lote']
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
    
    # Formata delta
    delta_str = f"{delta_ini:.2f}→{delta_fin:.2f}" if pd.notna(delta_ini) and pd.notna(delta_fin) else "-"
    
    # Formata parâmetros
    params = f"{limite_lote:.0f}/{pregoes_vol:.0f}" if pd.notna(limite_lote) and pd.notna(pregoes_vol) else "-"
    
    # Formata valores
    strike_str = f"{strike}" if isinstance(strike, str) else f"{strike:.2f}"
    ajustes_str = f"{num_ajustes:.0f}" if pd.notna(num_ajustes) else "-"
    saldo_str = f"{saldo_final}" if isinstance(saldo_final, str) else f"{saldo_final:.2f}"
    
    latex_table += f"{opcao} & {strike_str} & {periodo} & {delta_str} & {params} & {ajustes_str} & {saldo_str} \\\\\n"

latex_table += "\\hline\n"
latex_table += "\\end{tabular}\n"
latex_table += "\\end{table}"

print(latex_table) 