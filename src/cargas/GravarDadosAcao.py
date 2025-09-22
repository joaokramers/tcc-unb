import pandas as pd
import sqlite3
from datetime import datetime

def conectar_banco():
    return sqlite3.connect('banco/mercado_opcoes.db')

def gravar_dados_acao():
    # Conectar ao banco de dados
    conn = conectar_banco()
    cursor = conn.cursor()
    
    # Primeiro, verificar se o ativo PETR4 existe, se não, criar
    cursor.execute("SELECT id FROM ATIVO WHERE ticker = 'PETR4'")
    resultado = cursor.fetchone()
    
    if resultado is None:
        cursor.execute("INSERT INTO ATIVO (ticker, empresa) VALUES (?, ?)", ('PETR4', 'Petrobras PN'))
        id_ativo = cursor.lastrowid
    else:
        id_ativo = resultado[0]
        
        # Apagar dados existentes da Petrobras
        cursor.execute("DELETE FROM HIST_ATIVO WHERE id_ativo = ?", (id_ativo,))
        print(f"Dados antigos da Petrobras foram removidos.")
    
    # Ler o arquivo Excel
    try:
        df = pd.read_excel('dados/dados_petrobras_3anos.xlsx')
        
        # Preparar os dados para inserção
        dados_para_inserir = []
        for _, row in df.iterrows():
            # Converter a data para o formato correto
            data = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
            
            dados_para_inserir.append((
                id_ativo,
                data,
                float(row['Abertura']),
                float(row['Fechamento']),
                float(row['Máxima']),
                float(row['Mínima'])
            ))
        
        # Inserir os dados na tabela HIST_ATIVO
        cursor.executemany('''
            INSERT INTO HIST_ATIVO (id_ativo, data, abertura, fechamento, maximo, minimo)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', dados_para_inserir)
        
        # Commit das alterações
        conn.commit()
        print(f"Dados gravados com sucesso! {len(dados_para_inserir)} registros inseridos.")
        
    except FileNotFoundError:
        print("Erro: Arquivo 'dados/dados_petrobras_3anos.xlsx' não encontrado.")
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    gravar_dados_acao()
