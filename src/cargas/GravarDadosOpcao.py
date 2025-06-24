import os
import sqlite3
from datetime import datetime, timedelta
import re
import csv

def conectar_banco():
    return sqlite3.connect('banco/mercado_opcoes.db')

def extrair_info_arquivo(nome_arquivo):
    # Exemplo: PETRE301Daily-29e26-1605.csv
    partes = nome_arquivo.replace('.csv', '').split('-')
    
    # Extrair ticker e limpar (manter apenas até o último número)
    ticker = partes[0]  # PETRE301Daily
    # Encontrar a posição do último número
    ultimo_numero = max([i for i, c in enumerate(ticker) if c.isdigit()])
    ticker = ticker[:ultimo_numero + 1]  # PETRE301
    
    # Extrair strike (29e26 -> 29.26)
    strike_str = partes[1].replace('e', '.')
    strike = float(strike_str)
    
    # Extrair data de vencimento (1605 -> 16/05/2025)
    data_str = partes[2]
    dia = data_str[:2]
    mes = data_str[2:]
    vencimento = f"2025-{mes}-{dia}"  # Formato YYYY-MM-DD
    
    return ticker, strike, vencimento

def ler_dados_csv(caminho_arquivo):
    dados = []
    try:
        # Tentar primeiro com UTF-16
        with open(caminho_arquivo, 'r', encoding='utf-16') as arquivo:
            leitor = csv.reader(arquivo)
            for linha in leitor:
                if len(linha) >= 7:  # Garantir que a linha tem todos os campos necessários
                    data = datetime.strptime(linha[0], '%Y.%m.%d').strftime('%Y-%m-%d')
                    abertura = float(linha[1])
                    maximo = float(linha[2])
                    minimo = float(linha[3])
                    fechamento = float(linha[4])
                    dados.append((data, abertura, fechamento, maximo, minimo))
    except UnicodeError:
        # Se falhar, tentar com UTF-8
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            leitor = csv.reader(arquivo)
            for linha in leitor:
                if len(linha) >= 7:  # Garantir que a linha tem todos os campos necessários
                    data = datetime.strptime(linha[0], '%Y.%m.%d').strftime('%Y-%m-%d')
                    abertura = float(linha[1])
                    maximo = float(linha[2])
                    minimo = float(linha[3])
                    fechamento = float(linha[4])
                    dados.append((data, abertura, fechamento, maximo, minimo))
    return dados

def gravar_dados_opcao():
    conn = conectar_banco()
    cursor = conn.cursor()
    
    # Diretório onde estão os arquivos CSV
    diretorio = 'dados'
    
    try:
        # Limpar as tabelas antes de inserir novos dados
        print("Limpando tabelas existentes...")
        cursor.execute('DELETE FROM HIST_OPCAO')
        cursor.execute('DELETE FROM OPCAO')
        cursor.execute('DELETE FROM SIMULACAO')
        print("Tabelas limpas com sucesso!")
        
        # Listar todos os arquivos CSV que começam com PETRE ou PETRF
        arquivos = [f for f in os.listdir(diretorio) if (f.startswith('PETRE') or f.startswith('PETRF')) and f.endswith('.csv')]
        
        for arquivo in arquivos:
            # Extrair informações do nome do arquivo
            ticker, strike, vencimento = extrair_info_arquivo(arquivo)
            
            # Inserir a nova opção
            cursor.execute('''
                INSERT INTO OPCAO (id_ativo, tipo, ticker, strike, vencimento)
                VALUES (?, ?, ?, ?, ?)
            ''', (1, 'CALL', ticker, strike, vencimento))
            
            # Obter o ID da opção recém-inserida
            id_opcao = cursor.lastrowid
            
            # Ler e inserir os dados históricos
            caminho_arquivo = os.path.join(diretorio, arquivo)
            dados_historicos = ler_dados_csv(caminho_arquivo)
            
            # Preparar os dados para inserção
            dados_para_inserir = [(id_opcao, data, abertura, fechamento, maximo, minimo) 
                                for data, abertura, fechamento, maximo, minimo in dados_historicos]
            
            # Inserir os dados históricos
            cursor.executemany('''
                INSERT INTO HIST_OPCAO (id_opcao, data, abertura, fechamento, maximo, minimo)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', dados_para_inserir)
            
            # Determinar data de início e fim para a simulação
            data_vencimento = datetime.strptime(vencimento, '%Y-%m-%d').date()
            ano_vencimento = data_vencimento.year
            
            # Data de término: último dia antes do vencimento com negociação
            # Buscar todas as datas disponíveis e encontrar a última antes do vencimento
            datas_disponiveis = [datetime.strptime(data, '%Y-%m-%d').date() for data, _, _, _, _ in dados_historicos]
            datas_antes_vencimento = [data for data in datas_disponiveis if data < data_vencimento]
            
            if datas_antes_vencimento:
                data_termino = max(datas_antes_vencimento)
            else:
                # Se não encontrar datas antes do vencimento, usar a última data disponível
                data_termino = max(datas_disponiveis) if datas_disponiveis else None
            
            # Data de início: primeiro dia do ano do vencimento com negociação
            # Buscar a primeira data disponível no ano do vencimento
            datas_ano = [data for data, _, _, _, _ in dados_historicos 
                        if datetime.strptime(data, '%Y-%m-%d').year == ano_vencimento]
            
            if datas_ano:
                data_inicio = min(datas_ano)
            else:
                # Se não encontrar dados no ano do vencimento, usar a primeira data disponível
                data_inicio = dados_historicos[0][0] if dados_historicos else None
            
            if data_inicio and data_termino:
                # Inserir simulação
                cursor.execute('''
                    INSERT INTO SIMULACAO (id_opcao, quantidade, cenario, data_inicio, data_termino)
                    VALUES (?, ?, ?, ?, ?)
                ''', (id_opcao, 1000, 'DH', data_inicio, data_termino.strftime('%Y-%m-%d')))
                
                print(f"Opção inserida: {ticker} - Strike: {strike} - Vencimento: {vencimento}")
                print(f"  - {len(dados_historicos)} registros históricos inseridos")
                print(f"  - Simulação criada: {data_inicio} até {data_termino}")
            else:
                print(f"Erro: Não foi possível determinar datas para {ticker}")
        
        # Commit das alterações
        conn.commit()
        print(f"\nTotal de {len(arquivos)} opções processadas com sucesso!")
        
    except Exception as e:
        print(f"Erro ao processar os arquivos: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    gravar_dados_opcao() 