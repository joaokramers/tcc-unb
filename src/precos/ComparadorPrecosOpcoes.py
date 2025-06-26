import sys
import os

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
import pandas as pd
from helper.TradeHelper import TradeHelper

# Constante para o ID da simulação
ID_SIMULACAO =5

class ComparadorPrecosOpcoes:
    def __init__(self, conn: sqlite3.Connection, id_simulacao: int, pregoes_volatilidade: int = 30,
                 taxa_juros: float = 0.15):
        """
        Inicializa a classe ComparadorPrecosOpcoes.
        
        Args:
            conn: Conexão com o banco de dados SQLite
            id_simulacao: ID da simulação na tabela SIMULACAO
            pregoes_volatilidade: Número de pregões para cálculo da volatilidade (padrão: 30)
            taxa_juros: Taxa de juros anual (padrão: 15%)
        """
        self.conn = conn
        self.id_simulacao = id_simulacao
        self.pregoes_volatilidade = pregoes_volatilidade
        self.taxa_juros = taxa_juros
        
        # Recupera os dados da simulação
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT data_inicio, data_termino, id_opcao
            FROM SIMULACAO
            WHERE id = ?
        """, (id_simulacao,))
        
        simulacao = cursor.fetchone()
        if not simulacao:
            raise ValueError(f"Simulação com ID {id_simulacao} não encontrada.")
            
        self.data_inicio = datetime.strptime(simulacao[0], "%Y-%m-%d").date()
        self.data_termino = datetime.strptime(simulacao[1], "%Y-%m-%d").date()
        self.id_opcao = simulacao[2]
        
        # Recupera o preço de exercício, ID do ativo, ticker do ativo e data de vencimento da opção
        cursor.execute("""
            SELECT o.strike, o.id_ativo, a.ticker, o.vencimento
            FROM OPCAO o
            JOIN ATIVO a ON a.id = o.id_ativo
            WHERE o.id = ?
        """, (self.id_opcao,))
        
        opcao = cursor.fetchone()
        if not opcao:
            raise ValueError(f"Opção com ID {self.id_opcao} não encontrada.")
        
        self.preco_exercicio = opcao[0]
        self.id_ativo = opcao[1]
        self.ticker_ativo = opcao[2]
        self.data_vencimento = datetime.strptime(opcao[3], "%Y-%m-%d").date()
        
        # Inicializa as listas de preços e datas
        self.precos_opcao = []
        self.precos_ativo = []
        self.datas = []
        
        # Recupera os dados históricos
        self._recuperar_dados_historicos()
    
    def _recuperar_dados_historicos(self):
        """
        Recupera os dados históricos de preços da opção e do ativo.
        """
        cursor = self.conn.cursor()
        
        # Recupera preços da opção
        cursor.execute("""
            SELECT h.data, h.abertura
            FROM HIST_OPCAO h
            JOIN OPCAO o ON h.id_opcao = o.id
            WHERE o.id = ?
              AND h.data BETWEEN ? AND ?
            ORDER BY h.data ASC
        """, (self.id_opcao, self.data_inicio, self.data_termino))
        
        self.precos_opcao = cursor.fetchall()
        
        # Recupera preços do ativo
        cursor.execute("""
            SELECT h.data, h.abertura
            FROM HIST_ATIVO h
            JOIN ATIVO a ON h.id_ativo = a.id
            WHERE a.id = ?
              AND h.data BETWEEN ? AND ?
            ORDER BY h.data ASC
        """, (self.id_ativo, self.data_inicio, self.data_termino))
        
        self.precos_ativo = cursor.fetchall()
        
        # Verifica se os dados foram recuperados corretamente
        if not self.precos_opcao or not self.precos_ativo:
            raise ValueError("Não foi possível recuperar os dados históricos.")
        
        # Verifica se as datas correspondem
        datas_opcao = [row[0] for row in self.precos_opcao]
        datas_ativo = [row[0] for row in self.precos_ativo]
        
        if datas_opcao != datas_ativo:
            raise ValueError("As datas dos preços da opção e do ativo não correspondem.")
    
    def processar(self):
        """
        Processa o cálculo dos preços teóricos e compara com os preços de mercado.
        """
        self.datas = []
        self.precos_mercado = []
        self.precos_bs = []
        self.deltas = []
        self.diferenca_percentual = []
        
        for data_str, preco_ativo in self.precos_ativo:
            # Converte a data para datetime.date
            data = datetime.strptime(data_str, "%Y-%m-%d").date()
            
            # Encontra o preço da opção correspondente
            preco_opcao = next((row[1] for row in self.precos_opcao if row[0] == data_str), None)
            if preco_opcao is None:
                continue
            
            # Calcula o número de dias úteis até o vencimento
            dias_ate_vencimento = TradeHelper.calcular_dias_uteis(
                self.conn,
                self.id_ativo,
                data,
                self.data_vencimento
            )
            
            # Calcula o tempo anualizado
            tempo_anualizado = dias_ate_vencimento / 252  # Considerando 252 dias úteis
            
            # Calcula a volatilidade para a data atual
            sigma = TradeHelper.recuperaVolatilidadeAnualPara_x_Pregoes(
                self.conn,
                self.pregoes_volatilidade,
                self.ticker_ativo,
                data_str
            )
            
            # Calcula o preço teórico da call usando Black-Scholes
            preco_bs = TradeHelper.calcular_preco_call_black_scholes(
                S=preco_ativo,
                K=self.preco_exercicio,
                T=tempo_anualizado,
                r=self.taxa_juros,
                sigma=sigma
            )
            
            # Calcula o delta da call
            delta = TradeHelper.calcular_delta(
                opcao='call',
                S=preco_ativo,
                K=self.preco_exercicio,
                T=tempo_anualizado,
                r=self.taxa_juros,
                sigma=sigma
            )
            
            # Calcula a diferença percentual
            diferenca_percentual = ((preco_opcao - preco_bs) / preco_bs) * 100
            
            # Armazena os resultados
            self.datas.append(data_str)
            self.precos_mercado.append(preco_opcao)
            self.precos_bs.append(preco_bs)
            self.deltas.append(delta)
            self.diferenca_percentual.append(diferenca_percentual)
    
    def listar_dados(self) -> pd.DataFrame:
        """
        Lista os dados em formato de tabela.
        
        Returns:
            pd.DataFrame: DataFrame com as colunas:
                - Data
                - Preço Ação
                - Preço Mercado
                - Preço BS
                - Delta
                - Diferença %
        """
        # Cria um DataFrame com os dados
        df = pd.DataFrame({
            'Data': self.datas,
            'Preço Ação': [row[1] for row in self.precos_ativo],
            'Preço Mercado': self.precos_mercado,
            'Preço BS': self.precos_bs,
            'Delta': self.deltas,
            'Diferença %': self.diferenca_percentual
        })
        
        # Formata as colunas numéricas
        df['Preço Ação'] = df['Preço Ação'].map('R$ {:.2f}'.format)
        df['Preço Mercado'] = df['Preço Mercado'].map('R$ {:.2f}'.format)
        df['Preço BS'] = df['Preço BS'].map('R$ {:.2f}'.format)
        df['Delta'] = df['Delta'].map('{:.4f}'.format)
        df['Diferença %'] = df['Diferença %'].map('{:.2f}%'.format)
        
        return df
    
    def imprimir_dados(self):
        """
        Imprime os dados da comparação em formato de tabela.
        """
        # Recupera os dados da opção
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, strike, vencimento
            FROM OPCAO
            WHERE id = ?
        """, (self.id_opcao,))
        
        opcao = cursor.fetchone()
        if not opcao:
            raise ValueError(f"Opção com ID {self.id_opcao} não encontrada.")
            
        ticker, strike, vencimento = opcao
        
        # Calcula a volatilidade para a primeira data
        sigma = TradeHelper.recuperaVolatilidadeAnualPara_x_Pregoes(
            self.conn,
            self.pregoes_volatilidade,
            self.ticker_ativo,
            self.data_inicio.strftime("%Y-%m-%d")
        )
        
        # Imprime os dados da opção
        print("\nDados da Opção:")
        print("==================================================")
        print(f"Ticker: {ticker}")
        print(f"Strike: R$ {strike:.2f}")
        print(f"Vencimento: {vencimento}")
        print(f"Pregões de Volatilidade: {self.pregoes_volatilidade}")
        print(f"Volatilidade: {sigma*100:.1f}%")
        print(f"Taxa de Juros: {self.taxa_juros*100:.1f}%")
        print("==================================================\n")
        
        # Imprime os dados da comparação
        print("Comparação de Preços:")
        print("================================================================================")
        
        df = self.listar_dados()
        print(df.to_string(index=False))
        print("================================================================================")
        
        print(f"\nTotal de dias: {len(df)}")
        print(f"Diferença Média: {df['Diferença %'].str.rstrip('%').astype(float).mean():.2f}%")

if __name__ == "__main__":
    # Conecta ao banco de dados
    caminho_banco = 'banco/mercado_opcoes.db'
    conn = sqlite3.connect(caminho_banco)
    
    try:
        # Busca os dados da simulação
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, data_inicio, data_termino
            FROM SIMULACAO
            WHERE id = ?
        """, (ID_SIMULACAO,))
        
        simulacao = cursor.fetchone()
        if not simulacao:
            raise ValueError(f"Simulação com ID {ID_SIMULACAO} não encontrada.")
        
        data_inicio = datetime.strptime(simulacao[1], "%Y-%m-%d").date()
        data_termino = datetime.strptime(simulacao[2], "%Y-%m-%d").date()
        
        print(f"\nTestando ComparadorPrecosOpcoes com simulação ID {ID_SIMULACAO}")
        print(f"Período: {data_inicio} até {data_termino}")
        
        # Cria e processa a comparação
        comparador = ComparadorPrecosOpcoes(
            conn=conn,
            id_simulacao=ID_SIMULACAO,
            pregoes_volatilidade=30,  # x pregões para cálculo da volatilidade
            taxa_juros=0.15          # 15% ao ano
        )
        
        # Processa os dados
        comparador.processar()
        
        # Imprime os resultados
        comparador.imprimir_dados()
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")
    
    finally:
        # Fecha a conexão com o banco de dados
        conn.close() 