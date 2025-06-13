import sqlite3
import os

def criar_banco():
    # Conectar ao banco de dados (será criado se não existir)
    conn = sqlite3.connect('banco/mercado_opcoes.db')
    cursor = conn.cursor()

    # Criar tabela ATIVO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ATIVO (
        id INTEGER PRIMARY KEY,
        ticker VARCHAR NOT NULL,
        empresa VARCHAR NOT NULL
    )
    ''')

    # Criar tabela HIST_ATIVO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS HIST_ATIVO (
        id INTEGER PRIMARY KEY,
        id_ativo INTEGER NOT NULL,
        data DATE NOT NULL,
        abertura FLOAT NOT NULL,
        fechamento FLOAT NOT NULL,
        maximo FLOAT NOT NULL,
        minimo FLOAT NOT NULL,
        FOREIGN KEY (id_ativo) REFERENCES ATIVO(id)
    )
    ''')

    # Criar tabela OPCAO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS OPCAO (
        id INTEGER PRIMARY KEY,
        id_ativo INTEGER NOT NULL,
        tipo VARCHAR NOT NULL,
        strike FLOAT NOT NULL,
        vencimento DATE NOT NULL,
        FOREIGN KEY (id_ativo) REFERENCES ATIVO(id)
    )
    ''')

    # Criar tabela HIST_OPCAO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS HIST_OPCAO (
        id INTEGER PRIMARY KEY,
        id_opcao INTEGER NOT NULL,
        data DATE NOT NULL,
        abertura FLOAT NOT NULL,
        fechamento FLOAT NOT NULL,
        maximo FLOAT NOT NULL,
        minimo FLOAT NOT NULL,
        FOREIGN KEY (id_opcao) REFERENCES OPCAO(id)
    )
    ''')

    # Criar tabela SIMULACAO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SIMULACAO (
        id INTEGER PRIMARY KEY,
        id_opcao INTEGER NOT NULL,
        data_inicio DATE NOT NULL,
        data_termino DATE NOT NULL,
        quantidade FLOAT NOT NULL,
        cenario TEXT NOT NULL,
        FOREIGN KEY (id_opcao) REFERENCES OPCAO(id)
    )
    ''')

    # Criar tabela RESULTADOS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS RESULTADOS (
        id INTEGER PRIMARY KEY,
        id_simulacao INTEGER NOT NULL,
        data DATE NOT NULL,
        preco_ativo FLOAT NOT NULL,
        valor_delta FLOAT NOT NULL,
        preco_opcao FLOAT NOT NULL,
        preco_opcao_simulacao FLOAT NOT NULL,
        qtd_ativo FLOAT NOT NULL,
        qtd_ajuste_diario FLOAT NOT NULL,
        fluxo_caixa FLOAT NOT NULL,
        saldo_portfolio FLOAT NOT NULL,
        FOREIGN KEY (id_simulacao) REFERENCES SIMULACAO(id)
    )
    ''')

    # Commit das alterações e fechar conexão
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Garantir que o diretório banco existe
    os.makedirs('banco', exist_ok=True)
    
    # Criar o banco de dados
    criar_banco()
    print("Banco de dados criado com sucesso em 'banco/mercado_opcoes.db'") 