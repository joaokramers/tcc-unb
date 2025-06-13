import sqlite3
from datetime import datetime

def conectar_banco():
    return sqlite3.connect('banco/mercado_opcoes.db')

def exemplo_select_basico():
    conn = conectar_banco()
    cursor = conn.cursor()
    
    # Exemplo 1: Selecionar todos os ativos
    print("\n1. Todos os ativos:")
    cursor.execute("SELECT * FROM ATIVO")
    ativos = cursor.fetchall()
    for ativo in ativos:
        print(f"ID: {ativo[0]}, Ticker: {ativo[1]}, Empresa: {ativo[2]}")
    
    # Exemplo 2: Selecionar com WHERE
    print("\n2. Ativos com ticker específico:")
    cursor.execute("SELECT * FROM ATIVO WHERE ticker = 'PETR4'")
    ativo = cursor.fetchone()
    if ativo:
        print(f"ID: {ativo[0]}, Ticker: {ativo[1]}, Empresa: {ativo[2]}")
    
    # Exemplo 3: JOIN entre ATIVO e HIST_ATIVO
    print("\n3. Histórico de preços de um ativo:")
    cursor.execute("""
        SELECT a.ticker, h.data, h.fechamento 
        FROM ATIVO a 
        JOIN HIST_ATIVO h ON a.id = h.id_ativo 
        WHERE a.ticker = 'PETR4'
        ORDER BY h.data DESC
        LIMIT 5
    """)
    historico = cursor.fetchall()
    for registro in historico:
        print(f"Ticker: {registro[0]}, Data: {registro[1]}, Fechamento: {registro[2]}")
    
    # Exemplo 4: Agregações
    print("\n4. Média de preços por ativo:")
    cursor.execute("""
        SELECT a.ticker, 
               AVG(h.fechamento) as media_preco,
               MAX(h.fechamento) as maximo,
               MIN(h.fechamento) as minimo
        FROM ATIVO a 
        JOIN HIST_ATIVO h ON a.id = h.id_ativo 
        GROUP BY a.ticker
    """)
    medias = cursor.fetchall()
    for media in medias:
        print(f"Ticker: {media[0]}, Média: {media[1]:.2f}, Máximo: {media[2]:.2f}, Mínimo: {media[3]:.2f}")
    
    # Exemplo 5: Subconsulta
    print("\n5. Opções com preço acima da média:")
    cursor.execute("""
        SELECT o.id, a.ticker, o.strike, o.vencimento
        FROM OPCAO o
        JOIN ATIVO a ON o.id_ativo = a.id
        WHERE o.strike > (
            SELECT AVG(strike) 
            FROM OPCAO
        )
    """)
    opcoes = cursor.fetchall()
    for opcao in opcoes:
        print(f"ID: {opcao[0]}, Ticker: {opcao[1]}, Strike: {opcao[2]}, Vencimento: {opcao[3]}")
    
    conn.close()

if __name__ == '__main__':
    exemplo_select_basico() 