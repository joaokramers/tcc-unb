import sqlite3

def conectar_banco():
    return sqlite3.connect('banco/mercado_opcoes.db')

def alterar_tabela_opcao():
    conn = conectar_banco()
    cursor = conn.cursor()
    
    try:
        # Adicionar a coluna ticker à tabela OPCAO
        cursor.execute('''
            ALTER TABLE OPCAO 
            ADD COLUMN ticker VARCHAR NOT NULL 
        ''')
        
        # Commit das alterações
        conn.commit()
        print("Coluna 'ticker' adicionada com sucesso à tabela OPCAO!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("A coluna 'ticker' já existe na tabela OPCAO.")
        else:
            print(f"Erro ao alterar a tabela: {str(e)}")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    alterar_tabela_opcao() 