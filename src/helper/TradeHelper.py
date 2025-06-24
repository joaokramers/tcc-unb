import sqlite3
import numpy as np
from datetime import datetime, timedelta, date
import math
from scipy.stats import norm

class TradeHelper:
    @staticmethod
    def recuperaVolatilidadeAnual(conn: sqlite3.Connection, ticker: str, data_referencia: str) -> float:
        """
        Calcula a volatilidade histórica anual baseada nos últimos 252 dias de retornos.
        
        Args:
            conn: Conexão com o banco de dados
            ticker: Ticker do ativo
            data_referencia: Data de referência para calcular a volatilidade (formato: YYYY-MM-DD)
            
        Returns:
            float: Volatilidade histórica anual em decimal (ex: 0.25 para 25%)
        """
        cursor = conn.cursor()
        
        # Converter a data de referência para datetime
        data_ref = datetime.strptime(data_referencia, '%Y-%m-%d')
        
        # Calcular a data inicial (252 dias antes da data de referência)
        data_inicial = data_ref - timedelta(days=252)
        
        # Buscar os preços de fechamento dos últimos 252 dias
        cursor.execute('''
            SELECT data, fechamento
            FROM HIST_ATIVO ha
            JOIN ATIVO a ON ha.id_ativo = a.id
            WHERE a.ticker = ?
            AND ha.data BETWEEN ? AND ?
            ORDER BY ha.data
        ''', (ticker, data_inicial.strftime('%Y-%m-%d'), data_referencia))
        
        # Obter os resultados
        resultados = cursor.fetchall()
        
        if len(resultados) < 2:
            raise ValueError(f"Dados insuficientes para calcular a volatilidade do ativo {ticker}")
        
        # Extrair os preços de fechamento
        precos = [float(preco) for _, preco in resultados]
        
        # Calcular os retornos diários
        retornos = np.array(precos[1:]) / np.array(precos[:-1]) - 1
        
        # Calcular a volatilidade anual
        # Multiplicamos por np.sqrt(252) para anualizar (252 dias úteis no ano)
        volatilidade = np.std(retornos) * np.sqrt(252)
        
        return float(volatilidade)

    @staticmethod
    def _recuperaVolatilidadeBase(conn: sqlite3.Connection, pregoes, ticker: str, data_referencia: str) -> tuple:
        """
        Método base para calcular volatilidade com base nos últimos N pregões.
        
        Args:
            conn: conexão com o banco SQLite
            pregoes: número de pregões para calcular a volatilidade
            ticker: ticker do ativo (ex: 'PETR4')
            data_referencia: data de referência (formato: YYYY-MM-DD)
            
        Returns:
            tuple: (retornos, volatilidade_diaria)
        """
        cursor = conn.cursor()
        data_ref = datetime.strptime(data_referencia, '%Y-%m-%d')
        data_inicial = data_ref - timedelta(days=pregoes*2)  # garante folga para pelo o dobro de pregões

        # Seleciona os últimos fechamentos antes ou igual à data de referência
        cursor.execute('''
            SELECT ha.data, ha.fechamento
            FROM HIST_ATIVO ha
            JOIN ATIVO a ON ha.id_ativo = a.id
            WHERE a.ticker = ?
            AND ha.data <= ?
            AND ha.data >= ?
            ORDER BY ha.data DESC
            LIMIT ?
        ''', (ticker, data_referencia, data_inicial.strftime('%Y-%m-%d'), pregoes))

        resultados = cursor.fetchall()

        if len(resultados) < pregoes:
            raise ValueError(f"Dados insuficientes para calcular a volatilidade de {pregoes} pregões para {ticker}")

        # Reverte para ordem cronológica
        precos = [float(preco) for _, preco in reversed(resultados)]

        # Retornos percentuais diários
        retornos = np.array(precos[1:]) / np.array(precos[:-1]) - 1

        # Volatilidade diária (sem anualização)
        volatilidade_diaria = np.std(retornos)

        return retornos, volatilidade_diaria

    @staticmethod
    def recuperaVolatilidadeAnualPara_x_Pregoes(conn: sqlite3.Connection, pregoes, ticker: str, data_referencia: str) -> float:
        """
        Calcula a volatilidade anualizada com base nos últimos N pregões.
        
        Args:
            conn: conexão com o banco SQLite
            pregoes: número de pregões para calcular a volatilidade
            ticker: ticker do ativo (ex: 'PETR4')
            data_referencia: data de referência (formato: YYYY-MM-DD)
            
        Returns:
            Volatilidade histórica anualizada (ex: 0.22 para 22%)
        """
        _, volatilidade_diaria = TradeHelper._recuperaVolatilidadeBase(conn, pregoes, ticker, data_referencia)
        
        # Anualiza com fator sqrt(252)
        volatilidade_anual = volatilidade_diaria * np.sqrt(252)
        
        return float(volatilidade_anual)

    @staticmethod
    def recuperaVolatilidadeDiariaPara_x_Pregoes(conn: sqlite3.Connection, pregoes, ticker: str, data_referencia: str) -> float:
        """
        Calcula a volatilidade diária (não anualizada) com base nos últimos N pregões.
        
        Args:
            conn: conexão com o banco SQLite
            pregoes: número de pregões para calcular a volatilidade
            ticker: ticker do ativo (ex: 'PETR4')
            data_referencia: data de referência (formato: YYYY-MM-DD)
            
        Returns:
            Volatilidade histórica diária (não anualizada) (ex: 0.015 para 1.5% ao dia)
        """
        _, volatilidade_diaria = TradeHelper._recuperaVolatilidadeBase(conn, pregoes, ticker, data_referencia)
        
        return float(volatilidade_diaria)

    @staticmethod
    def calcular_dias_uteis(conn: sqlite3.Connection, id_ativo: int, data_inicio: date, data_fim: date) -> int:
        """
        Calcula a quantidade de dias úteis entre duas datas, excluindo o último dia.
        
        Args:
            conn: Conexão com o banco de dados SQLite
            id_ativo: ID do ativo
            data_inicio: Data inicial
            data_fim: Data final
            
        Returns:
            int: Número de dias úteis entre as datas (excluindo o último dia)
        """
        cursor = conn.cursor()
        
        # Busca todos os dias úteis entre as datas
        cursor.execute("""
            SELECT COUNT(DISTINCT data)
            FROM HIST_ATIVO
            WHERE id_ativo = ?
              AND data BETWEEN ? AND ?
        """, (id_ativo, data_inicio, data_fim))
        
        total_dias = cursor.fetchone()[0]
        
        # Subtrai 1 para excluir o último dia
        return max(0, total_dias - 1)

    @staticmethod
    def preco_futuro(S: float, mu: float, sigma: float, dt: float, z=None,seed=None) -> float:
        """
        Calcula o preço futuro usando o modelo de movimento browniano geométrico.
        
        Args:
            S: Preço atual
            mu: Retorno médio anual
            sigma: Volatilidade anual
            dt: Incremento de tempo em anos
            z: Valor da distribuição normal padrão
            
        Returns:
            float: Preço futuro
        """

        if seed is not None:
           np.random.seed(seed)

        if z is None:   
           z = np.random.normal()

        return S * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)

    @staticmethod
    def calcular_delta(opcao: str, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calcula o delta de uma opção usando o modelo Black-Scholes.
        
        Args:
            opcao: Tipo da opção ('call' ou 'put')
            S: Preço atual do ativo
            K: Preço de exercício
            T: Tempo até o vencimento em anos
            r: Taxa de juros livre de risco
            sigma: Volatilidade
            
        Returns:
            float: Delta da opção
        """
        d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if opcao.lower() == 'call':
            return norm.cdf(d1)
        elif opcao.lower() == 'put':
            return norm.cdf(d1) - 1
        else:
            raise ValueError("Tipo de opção inválido. Use 'call' ou 'put'.")

    def rgbm(n, s0, mu, sigma, seed=None, ate_passo=None):
        """
        Simula o movimento browniano geométrico de forma recursiva (discreta).
        
        Args:
            n (int): número de passos
            s0 (float): valor inicial do ativo
            mu (float): retorno médio
            sigma (float): volatilidade
            seed (int): semente aleatória (opcional)
            ate_passo (int): até qual passo simular (se None, vai até n)
            
        Returns:
            list: trajetória do processo GBM

            dSt =  μSt dt + σSt dWt
            
        """
        if seed is not None:
            np.random.seed(seed)

        # Define até qual passo simular
        if ate_passo is None:
            ate_passo = n
        else:
            ate_passo = min(ate_passo, n)  # Não pode ir além de n

        s_k = [float(s0)]  # valor inicial
        dt = 1/n # incremento de tempo 
        for k in range(ate_passo):
            z = np.random.normal()
            next_val = s_k[k] + s_k[k] * (mu * dt + sigma * np.sqrt(dt) * z)
            s_k.append(next_val)
        return s_k

    @staticmethod
    def calcular_preco_call_black_scholes(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calcula o preço de uma opção de compra (CALL) pelo modelo de Black-Scholes.

        Args:
            S: Preço atual do ativo-objeto
            K: Preço de exercício (strike)
            T: Tempo até o vencimento (em anos)
            r: Taxa de juros livre de risco (anual, decimal)
            sigma: Volatilidade anual do ativo (decimal)

        Returns:
            float: Preço da opção de compra (CALL)
        """
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            raise ValueError("Todos os parâmetros devem ser positivos e T > 0.")

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        preco_call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return preco_call
