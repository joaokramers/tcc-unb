import yfinance as yf
import pandas as pd

# Define o ticker da Petrobras negociado na B3
ticker = "PETR4.SA"

# Baixa os dados históricos dos últimos 3 anos
dados = yf.download(ticker, period="3y", interval="1d")

# Filtra apenas as colunas desejadas
dados_filtrados = dados[["Open", "High", "Low", "Close"]]

# Renomeia as colunas para português (opcional)
dados_filtrados.columns = ["Abertura", "Máxima", "Mínima", "Fechamento"]

# Arredonda para duas casas decimais
dados_filtrados = dados_filtrados.round(2)

# Salva em uma planilha Excel
arquivo_excel = ".\\dados\\dados_petrobras_3anos.xlsx"
dados_filtrados.to_excel(arquivo_excel, sheet_name="PETR4", engine="openpyxl")

print(f"Dados dos últimos 3 anos salvos em: {arquivo_excel}")