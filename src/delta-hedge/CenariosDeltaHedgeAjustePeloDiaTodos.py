import sys
import os
import numpy as np

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
from DeltaHedgeAjustePeloDia import DeltaHedgeAjustePeloDia

def executar_cenario(conn: sqlite3.Connection, id_simulacao: int, frequencia_ajuste: int = 1,
                    taxa_juros: float = 0.15, pregoes_volatilidade: int = 30, arquivo_saida=None):
    """
    Executa um cenário de simulação de delta hedge.
    
    Args:
        conn: Conexão com o banco de dados SQLite
        id_simulacao: ID da simulação na tabela SIMULACAO
        frequencia_ajuste: Frequência de ajuste em dias (padrão: 1 dia)
        taxa_juros: Taxa de juros anual (padrão: 6%)
        pregoes_volatilidade: Número de pregões para cálculo da volatilidade (padrão: 30)
        arquivo_saida: Arquivo para gravar os resultados
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
        
        resultado = f"\nTestando DeltaHedgeAjustePeloDia com simulação ID {id_simulacao}\n"
        resultado += f"Período: {data_inicio} até {data_termino}\n"
        resultado += f"Frequência de Ajuste: {frequencia_ajuste} dia(s)\n"
        resultado += f"Taxa de Juros: {taxa_juros*100:.1f}%\n"
        resultado += f"Pregões de Volatilidade: {pregoes_volatilidade}\n"
        resultado += "=" * 80 + "\n"
        
        print(resultado)
        if arquivo_saida:
            arquivo_saida.write(resultado)
        
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
        
        # Captura a saída da impressão
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            delta_hedge.imprimir_dados()
        
        resultado_simulacao = f.getvalue()
        print(resultado_simulacao)
        if arquivo_saida:
            arquivo_saida.write(resultado_simulacao)
            arquivo_saida.flush()  # Força a escrita no arquivo
        
    except Exception as e:
        erro = f"\nErro durante a execução: {str(e)}\n"
        print(erro)
        if arquivo_saida:
            arquivo_saida.write(erro)

def executar_cenarios_para_simulacao(conn: sqlite3.Connection, id_simulacao: int, arquivo_saida=None):
    """
    Executa múltiplos cenários para uma simulação específica.
    
    Args:
        conn: Conexão com o banco de dados SQLite
        id_simulacao: ID da simulação na tabela SIMULACAO
        arquivo_saida: Arquivo para gravar os resultados
    """
    cabecalho = f"\n{'='*100}\n"
    cabecalho += f"EXECUTANDO CENÁRIOS PARA SIMULAÇÃO ID {id_simulacao}\n"
    cabecalho += f"{'='*100}\n"
    
    print(cabecalho)
    if arquivo_saida:
        arquivo_saida.write(cabecalho)
    
    # Lista de frequências de ajuste para testar
    frequencias_ajuste = [1, 3, 5, 7]
    
    # Lista de períodos de volatilidade para testar
    pregoes_volatilidade = [30, 60, 120, 252]
    
    # Executa todos os cenários combinando frequências de ajuste e períodos de volatilidade
    for frequencia in frequencias_ajuste:
        for pregoes in pregoes_volatilidade:
            separador = f"\n{'='*80}\n"
            separador += f"CENÁRIO: Frequência Ajuste = {frequencia} dia(s), Pregões Volatilidade = {pregoes}\n"
            separador += f"{'='*80}\n"
            
            print(separador)
            if arquivo_saida:
                arquivo_saida.write(separador)
            
            executar_cenario(
                conn=conn,
                id_simulacao=id_simulacao,
                frequencia_ajuste=frequencia,
                taxa_juros=0.15,
                pregoes_volatilidade=pregoes,
                arquivo_saida=arquivo_saida
            )

def main():
    # Conecta ao banco de dados
    caminho_banco = 'banco/mercado_opcoes.db'
    conn = sqlite3.connect(caminho_banco)
    
    # Abre arquivo para gravar resultados
    caminho_arquivo = 'dados/SimulacaoPeloDia.txt'
    with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo_saida:
        try:
            # Cabeçalho do arquivo
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cabecalho_arquivo = f"SIMULAÇÕES DE DELTA HEDGE - AJUSTE PELO DIA\n"
            cabecalho_arquivo += f"Data/Hora de Execução: {timestamp}\n"
            cabecalho_arquivo += f"{'='*100}\n\n"
            
            arquivo_saida.write(cabecalho_arquivo)
            print(cabecalho_arquivo)
            
            # Lista todas as simulações disponíveis
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.data_inicio, s.data_termino, o.ticker, o.strike, o.vencimento
                FROM SIMULACAO s
                JOIN OPCAO o ON o.id = s.id_opcao
                ORDER BY s.id ASC
            """)
            
            simulacoes = cursor.fetchall()
            if not simulacoes:
                raise ValueError("Nenhuma simulação encontrada no banco de dados.")
            
            info_simulacoes = "\nSimulações disponíveis:\n"
            info_simulacoes += "=" * 80 + "\n"
            for sim in simulacoes:
                info_simulacoes += f"ID: {sim[0]}\n"
                info_simulacoes += f"Período: {sim[1]} até {sim[2]}\n"
                info_simulacoes += f"Opção: {sim[3]} - Strike: R$ {sim[4]:.2f} - Vencimento: {sim[5]}\n"
                info_simulacoes += "-" * 80 + "\n"
            
            info_simulacoes += f"\nTotal de simulações encontradas: {len(simulacoes)}\n"
            info_simulacoes += f"Executando cenários para todas as simulações...\n\n"
            
            print(info_simulacoes)
            arquivo_saida.write(info_simulacoes)
            
            # Executa para todas as simulações
            for i, sim in enumerate(simulacoes, 1):
                id_simulacao = sim[0]
                progresso = f"\nProcessando simulação {i}/{len(simulacoes)} (ID: {id_simulacao})\n"
                print(progresso)
                arquivo_saida.write(progresso)
                
                try:
                    executar_cenarios_para_simulacao(conn, id_simulacao, arquivo_saida)
                except Exception as e:
                    erro = f"\nErro ao processar simulação ID {id_simulacao}: {str(e)}\n"
                    print(erro)
                    arquivo_saida.write(erro)
                    continue
            
            # Rodapé do arquivo
            rodape = f"\n{'='*100}\n"
            rodape += "EXECUÇÃO CONCLUÍDA PARA TODAS AS SIMULAÇÕES\n"
            rodape += f"{'='*100}\n"
            
            print(rodape)
            arquivo_saida.write(rodape)
            
        except Exception as e:
            erro = f"\nErro durante a execução: {str(e)}\n"
            print(erro)
            arquivo_saida.write(erro)
        
        finally:
            # Fecha a conexão com o banco de dados
            conn.close()
    
    print(f"\nResultados salvos em: {caminho_arquivo}")

if __name__ == "__main__":
    main() 