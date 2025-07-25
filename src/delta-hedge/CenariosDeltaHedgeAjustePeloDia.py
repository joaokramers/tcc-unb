import sys
import os
import numpy as np

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
from DeltaHedgeAjustePeloDia import DeltaHedgeAjustePeloDia

# Constante para o ID da simulação
ID_SIMULACAO = 1

def executar_cenario(conn: sqlite3.Connection, id_simulacao: int, frequencia_ajuste: int = 1,
                    taxa_juros: float = 0.15, pregoes_volatilidade: int = 30):
    """
    Executa um cenário de simulação de delta hedge.
    
    Args:
        conn: Conexão com o banco de dados SQLite
        id_simulacao: ID da simulação na tabela SIMULACAO
        frequencia_ajuste: Frequência de ajuste em dias (padrão: 1 dia)
        taxa_juros: Taxa de juros anual (padrão: 6%)
        pregoes_volatilidade: Número de pregões para cálculo da volatilidade (padrão: 30)
    """
    try:
        # Busca os dados da simulação
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, data_inicio, data_termino
            FROM SIMULACAO
            WHERE id = ?
        """, (id_simulacao,))
        
        simulacao = cursor.fetchone()
        if not simulacao:
            raise ValueError(f"Simulação com ID {id_simulacao} não encontrada.")
        
        data_inicio = datetime.strptime(simulacao[1], "%Y-%m-%d").date()
        data_termino = datetime.strptime(simulacao[2], "%Y-%m-%d").date()
        
        print(f"\nTestando DeltaHedge com simulação ID {id_simulacao}")
        print(f"Período: {data_inicio} até {data_termino}")
        print(f"Frequência de Ajuste: {frequencia_ajuste} dia(s)")
        print(f"Taxa de Juros: {taxa_juros*100:.1f}%")
        print(f"Pregões de Volatilidade: {pregoes_volatilidade}")
        print("=" * 80)
        
        # Cria e processa a simulação
        delta_hedge = DeltaHedgeAjustePeloDia(
            conn=conn,
            id_simulacao=id_simulacao,
            frequencia_ajuste=frequencia_ajuste,
            taxa_juros=taxa_juros,
            pregoes_volatilidade=pregoes_volatilidade
        )
        
        # Processa os dados
        delta_hedge.processar()
        
        # Imprime os resultados
        delta_hedge.imprimir_dados()
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")

def main():
    # Conecta ao banco de dados
    caminho_banco = 'banco/mercado_opcoes.db'
    conn = sqlite3.connect(caminho_banco)
    
    try:
        # Lista todas as simulações disponíveis
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.data_inicio, s.data_termino, o.ticker, o.strike, o.vencimento
            FROM SIMULACAO s
            JOIN OPCAO o ON o.id = s.id_opcao
            ORDER BY s.id DESC
        """)
        
        simulacoes = cursor.fetchall()
        if not simulacoes:
            raise ValueError("Nenhuma simulação encontrada no banco de dados.")
        
        print("\nSimulações disponíveis:")
        print("=" * 80)
        for sim in simulacoes:
            print(f"ID: {sim[0]}")
            print(f"Período: {sim[1]} até {sim[2]}")
            print(f"Opção: {sim[3]} - Strike: R$ {sim[4]:.2f} - Vencimento: {sim[5]}")
            print("-" * 80)
        
        # Exemplo de execução de diferentes cenários
        print("\nExecutando cenários de teste...")
        
        # Cenário 1: Ajuste diário
        executar_cenario(
            conn=conn,
            id_simulacao=ID_SIMULACAO,
            frequencia_ajuste=1,
            taxa_juros=0.15,
            pregoes_volatilidade=30
        )
        
        # Cenário 2: Ajuste a cada 3 dias
        executar_cenario(
            conn=conn,
            id_simulacao=ID_SIMULACAO,
            frequencia_ajuste=3,
            taxa_juros=0.15,
            pregoes_volatilidade=30
        )
        
        # Cenário 3: Ajuste a cada 5 dias
        executar_cenario(
            conn=conn,
            id_simulacao=ID_SIMULACAO,
            frequencia_ajuste=5,
            taxa_juros=0.15,
            pregoes_volatilidade=30
        )
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")
    
    finally:
        # Fecha a conexão com o banco de dados
        conn.close()

if __name__ == "__main__":
    main() 