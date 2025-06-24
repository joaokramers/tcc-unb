import sys
import os

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
import pandas as pd
from helper.TradeHelper import TradeHelper

class DeltaHedgeAjustePeloDia:
    def __init__(self, conn: sqlite3.Connection, id_simulacao: int, frequencia_ajuste: int = 1, 
                 taxa_juros: float = 0.06, pregoes_volatilidade: int = 30):
        """
        Inicializa a classe DeltaHedge.
        
        Args:
            conn: Conexão com o banco de dados SQLite
            id_simulacao: ID da simulação na tabela SIMULACAO
            frequencia_ajuste: Frequência de ajuste em dias (padrão: 1 dia)
            taxa_juros: Taxa de juros anual (padrão: 6%)
            pregoes_volatilidade: Número de pregões para cálculo da volatilidade (padrão: 30)
        """
        self.conn = conn
        self.id_simulacao = id_simulacao
        self.frequencia_ajuste = frequencia_ajuste
        self.taxa_juros = taxa_juros
        self.pregoes_volatilidade = pregoes_volatilidade
        
        # Recupera os dados da simulação
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT data_inicio, data_termino, id_opcao, quantidade
            FROM SIMULACAO
            WHERE id = ?
        """, (id_simulacao,))
        
        simulacao = cursor.fetchone()
        if not simulacao:
            raise ValueError(f"Simulação com ID {id_simulacao} não encontrada.")
            
        self.data_inicio = datetime.strptime(simulacao[0], "%Y-%m-%d").date()
        self.data_termino = datetime.strptime(simulacao[1], "%Y-%m-%d").date()
        self.id_opcao = simulacao[2]
        self.quantidade_opcoes = simulacao[3]  # Quantidade de opções a serem vendidas
        
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
        self.datas_ajuste = []
        self.deltas = []
        
        # Listas para o delta hedge
        self.diferenca_delta = []  # Diferença entre delta atual e anterior
        self.ajuste_saldo = []     # Valor do ajuste no saldo (positivo = entrada, negativo = saída)
        self.saldo_diario = []     # Saldo acumulado por dia
        self.qtd_acoes = []        # Lista para armazenar a quantidade de ações
        
        # Recupera os dados históricos
        self._recuperar_dados_historicos()
    
    def _recuperar_dados_historicos(self):
        """
        Recupera os dados históricos de preços da opção e do ativo.
        Também define as datas de ajuste baseado na frequência especificada.
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
        
        # Define as datas de ajuste baseado na frequência
        self.datas_ajuste = datas_ativo[::self.frequencia_ajuste]
        
        # Garante que a última data está incluída
        if self.datas_ajuste[-1] != datas_ativo[-1]:
            self.datas_ajuste.append(datas_ativo[-1])

    def processar(self):
        """
        Processa o cálculo dos deltas e implementa a estratégia de delta hedge.
        """
        self.deltas = []
        self.diferenca_delta = []
        self.ajuste_saldo = []
        self.saldo_diario = []
        self.datas_ajuste = []  # Lista para armazenar as datas de ajuste
        self.datas_ajuste_real = []  # Lista para armazenar as datas onde realmente houve ajuste
        self.qtd_acoes = []     # Lista para armazenar a quantidade de ações
        
        for i, (data_str, preco_ativo) in enumerate(self.precos_ativo):
            # Converte a data para datetime.date
            data = datetime.strptime(data_str, "%Y-%m-%d").date()
            
            # Verifica se é uma data de ajuste
            eh_ajuste = (i % self.frequencia_ajuste == 0)
            if eh_ajuste:
                self.datas_ajuste.append(data)
            
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
                self.ticker_ativo,  # Usa o ticker do ativo
                data_str
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
            
            self.deltas.append(delta)
            
            # Calcula a diferença de delta e o ajuste no saldo
            if i == 0:
                # Primeiro dia: vende opções e compra ações
                qtd_acoes = delta * self.quantidade_opcoes  # Quantidade de ações a comprar
                self.qtd_acoes.append(qtd_acoes)
                diferenca = qtd_acoes  # Diferença é a quantidade total pois começamos do zero
                self.diferenca_delta.append(diferenca)
                
                # Vende opções e compra ações
                valor_opcoes = self.quantidade_opcoes * self.precos_opcao[i][1]  # Valor recebido pela venda das opções
                valor_acoes = diferenca * preco_ativo  # Valor gasto na compra das ações
                ajuste = valor_opcoes - valor_acoes  # Saldo inicial
                
                # Primeiro dia sempre é ajuste
                self.datas_ajuste_real.append(data)
                
            else:
                # Dias seguintes: ajusta posição baseado na diferença de delta apenas se for dia de ajuste
                if eh_ajuste:
                    delta_anterior = self.deltas[i-1]
                    qtd_acoes_anterior = self.qtd_acoes[-1]
                    qtd_acoes_nova = delta * self.quantidade_opcoes
                    diferenca = qtd_acoes_nova - qtd_acoes_anterior
                    # Calcula o ajuste no saldo
                    ajuste = -diferenca * preco_ativo  # Negativo porque se comprar gasta, se vender recebe
                    
                    # Registra a data de ajuste real
                    self.datas_ajuste_real.append(data)
                else:
                    # Mantém a quantidade de ações do último ajuste
                    qtd_acoes_nova = self.qtd_acoes[-1]
                    diferenca = 0
                    ajuste = 0
                
                self.qtd_acoes.append(qtd_acoes_nova)
                self.diferenca_delta.append(diferenca)
            
            self.ajuste_saldo.append(ajuste)
            
            # Calcula o saldo acumulado
            saldo_anterior = self.saldo_diario[-1] if self.saldo_diario else 0
            self.saldo_diario.append(saldo_anterior + ajuste)
        
        # Verifica se o tamanho das listas corresponde ao número de datas
        if len(self.deltas) != len(self.precos_ativo):
            raise ValueError("Erro no cálculo dos deltas: número de valores não corresponde ao número de datas.")
    
    def listar_dados(self) -> pd.DataFrame:
        """
        Lista os dados em formato de tabela.
        
        Returns:
            pd.DataFrame: DataFrame com as colunas:
                - Data
                - Ativo
                - Opção
                - Delta
                - PregõesVencimento
                - Ajuste Ações
                - Qtd Ações
                - Ajuste Saldo
                - Saldo Acumulado
                - Saldo Real
                - Ajuste
        """
        # Cria um DataFrame com os dados
        df = pd.DataFrame({
            'Data': [row[0] for row in self.precos_ativo],
            'Ativo': [row[1] for row in self.precos_ativo],
            'Opção': [row[1] for row in self.precos_opcao],
            'Delta': self.deltas,
            'PregõesVencimento': [TradeHelper.calcular_dias_uteis(
                self.conn,
                self.id_ativo,
                datetime.strptime(x, "%Y-%m-%d").date(),
                self.data_vencimento
            ) for x in [row[0] for row in self.precos_ativo]],
            'Ajuste Ações': self.diferenca_delta,
            'Qtd Ações': self.qtd_acoes,
            'Ajuste Saldo': self.ajuste_saldo,
            'Saldo Acumulado': self.saldo_diario,
            'Ajuste': [datetime.strptime(data, "%Y-%m-%d").date() in self.datas_ajuste_real for data in [row[0] for row in self.precos_ativo]]
        })
        
        # Calcula o saldo real (saldo acumulado + valor das ações - valor das opções)
        df['Saldo Real'] = df['Saldo Acumulado'] + (df['Qtd Ações'] * df['Ativo']) - (self.quantidade_opcoes * df['Opção'])
        
        # Formata as colunas numéricas
        df['Ativo'] = df['Ativo'].map('R$ {:.2f}'.format)
        df['Opção'] = df['Opção'].map('R$ {:.2f}'.format)
        df['Delta'] = df['Delta'].map('{:.4f}'.format)
        df['Ajuste Ações'] = df['Ajuste Ações'].map('{:.2f}'.format)
        df['Qtd Ações'] = df['Qtd Ações'].map('{:.2f}'.format)
        df['Ajuste Saldo'] = df['Ajuste Saldo'].map('R$ {:.2f}'.format)
        df['Saldo Acumulado'] = df['Saldo Acumulado'].map('R$ {:.2f}'.format)
        df['Saldo Real'] = df['Saldo Real'].map('R$ {:.2f}'.format)
        
        return df
    
    def imprimir_dados(self):
        """
        Imprime os dados da simulação em formato de tabela.
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
        
        # Imprime os dados da opção
        print("\nDados da Opção:")
        print("==================================================")
        print(f"Ticker: {ticker}")
        print(f"Strike: R$ {strike:.2f}")
        print(f"Vencimento: {vencimento}")
        print(f"Quantidade Vendida: {self.quantidade_opcoes}")
        print(f"Frequência de Ajuste: {self.frequencia_ajuste} dia(s)")
        print("==================================================\n")
        
        # Imprime os dados da simulação
        print("Dados da Simulação de Delta Hedge:")
        print("================================================================================")
        
        df = self.listar_dados()
        print(df.to_string(index=False))
        print("================================================================================")
        
        print(f"\nTotal de dias: {len(df)}")
        print(f"Total de ajustes: {len(self.datas_ajuste_real)}")
        print(f"Taxa de juros: {self.taxa_juros*100:.1f}%")
        print(f"Pregões de Volatilidade: {self.pregoes_volatilidade}")

if __name__ == "__main__":
    # Conecta ao banco de dados
    caminho_banco = 'banco/mercado_opcoes.db'
    conn = sqlite3.connect(caminho_banco)
    
    try:
        # Busca uma simulação existente
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, data_inicio, data_termino
            FROM SIMULACAO
            ORDER BY id DESC
            LIMIT 1
        """)
        
        simulacao = cursor.fetchone()
        if not simulacao:
            raise ValueError("Nenhuma simulação encontrada no banco de dados.")
        
        id_simulacao = simulacao[0]
        data_inicio = datetime.strptime(simulacao[1], "%Y-%m-%d").date()
        data_termino = datetime.strptime(simulacao[2], "%Y-%m-%d").date()
        
        print(f"\nTestando DeltaHedge com simulação ID {id_simulacao}")
        print(f"Período: {data_inicio} até {data_termino}")
        
        # Cria e processa a simulação
        delta_hedge = DeltaHedgeAjustePeloDia(
            conn=conn,
            id_simulacao=id_simulacao,
            frequencia_ajuste=5,  # Ajuste a cada x dias
            taxa_juros=0.06,      # 6% ao ano
            pregoes_volatilidade=10  # x pregões para cálculo da volatilidade
        )
        
        # Processa os dados
        delta_hedge.processar()
        
        # Imprime os resultados
        delta_hedge.imprimir_dados()
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")
    
    finally:
        # Fecha a conexão com o banco de dados
        conn.close() 