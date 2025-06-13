import unittest
import sqlite3
import os
import numpy as np
from datetime import datetime, timedelta
from TradeHelper import TradeHelper

class TestTradeHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Conectar ao banco de dados real
        cls.conn = sqlite3.connect('banco/mercado_opcoes.db')
        cls.cursor = cls.conn.cursor()
        
        # Verificar se existem dados suficientes para o teste
        cls.cursor.execute('''
            SELECT COUNT(*) 
            FROM HIST_ATIVO ha
            JOIN ATIVO a ON ha.id_ativo = a.id
            WHERE a.ticker = 'PETR4'
        ''')
        
        quantidade_registros = cls.cursor.fetchone()[0]
        if quantidade_registros < 252:
            raise unittest.SkipTest("Dados insuficientes no banco para realizar o teste")
    
    def test_recuperaVolatilidadeAnual(self):
        # Obter a data mais recente disponível no banco
        self.cursor.execute('''
            SELECT MAX(data)
            FROM HIST_ATIVO ha
            JOIN ATIVO a ON ha.id_ativo = a.id
            WHERE a.ticker = 'PETR4'
        ''')
        
        data_referencia = self.cursor.fetchone()[0]
        
        # Calcular a volatilidade
        volatilidade = TradeHelper.recuperaVolatilidadeAnual(self.conn, 'PETR4', data_referencia)
        
        # Verificar se a volatilidade está dentro de um intervalo razoável
        # Para ações brasileiras, esperamos uma volatilidade anual entre 20% e 60%
        self.assertGreater(volatilidade, 0.20)
        self.assertLess(volatilidade, 0.60)
        
        print(f"\nVolatilidade anual calculada para PETR4 em {data_referencia}: {volatilidade:.2%}")
    
    def test_dados_insuficientes(self):
        # Testar com um ticker que não existe
        with self.assertRaises(ValueError):
            TradeHelper.recuperaVolatilidadeAnual(self.conn, 'INVALID', '2023-12-31')
    
    def test_calcular_delta_call(self):
        # Teste para opção de compra (call)
        S = 100.0  # Preço do ativo
        K = 100.0  # Strike
        T = 30/252  # 30 dias úteis
        r = 0.10    # Taxa de 10% ao ano
        sigma = 0.30  # Volatilidade de 30% ao ano
        
        delta = TradeHelper.calcular_delta("call", S, K, T, r, sigma)
        
        # Para uma call ATM (at-the-money), o delta deve estar próximo de 0.5
        self.assertGreater(delta, 0.43)
        self.assertLess(delta, 0.57)
        print(f"\nDelta da call ATM: {delta:.4f}")
    
    def test_calcular_delta_put(self):
        # Teste para opção de venda (put)
        S = 100.0  # Preço do ativo
        K = 100.0  # Strike
        T = 30/252  # 30 dias úteis
        r = 0.10    # Taxa de 10% ao ano
        sigma = 0.30  # Volatilidade de 30% ao ano
        
        delta = TradeHelper.calcular_delta("put", S, K, T, r, sigma)
        
        # Para uma put ATM, o delta deve estar próximo de -0.5
        self.assertGreater(delta, -0.58)
        self.assertLess(delta, -0.42)
        print(f"\nDelta da put ATM: {delta:.4f}")
    
    def test_calcular_delta_call_itm(self):
        # Teste para call in-the-money
        S = 110.0  # Preço do ativo
        K = 100.0  # Strike
        T = 30/252  # 30 dias úteis
        r = 0.10    # Taxa de 10% ao ano
        sigma = 0.30  # Volatilidade de 30% ao ano
        
        delta = TradeHelper.calcular_delta("call", S, K, T, r, sigma)
        
        # Para uma call ITM, o delta deve ser maior que 0.5
        self.assertGreater(delta, 0.5)
        self.assertLess(delta, 1.0)
        print(f"\nDelta da call ITM: {delta:.4f}")
    
    def test_calcular_delta_parametros_invalidos(self):
        # Teste com parâmetros inválidos
        with self.assertRaises(ValueError):
            TradeHelper.calcular_delta("call", 100.0, 100.0, 0, 0.10, 0.30)  # T = 0
        
        with self.assertRaises(ValueError):
            TradeHelper.calcular_delta("call", 100.0, 100.0, 30/252, 0.10, 0)  # sigma = 0
        
        with self.assertRaises(ValueError):
            TradeHelper.calcular_delta("invalid", 100.0, 100.0, 30/252, 0.10, 0.30)  # tipo inválido
    
    def test_preco_futuro_30dias(self):
        # Teste para 30 dias úteis
        S0 = 100.0  # Preço atual
        mu = 0.10   # Retorno médio de 10% ao ano
        sigma = 0.30  # Volatilidade de 30% ao ano
        t = 30/252  # 30 dias úteis
        
        # Usar um valor fixo de z para teste determinístico
        z = 0.0  # Valor médio da normal padrão
        
        preco_futuro = TradeHelper.preco_futuro(S0, mu, sigma, t, z)
        
        # O preço futuro deve ser maior que o preço atual (com z = 0)
        self.assertGreater(preco_futuro, S0)
        
        # Com z = 0, o crescimento deve ser aproximadamente 0.65%
        # Fórmula: exp((mu - 0.5*sigma^2)*t)
        crescimento_esperado = np.exp((mu - 0.5 * sigma**2) * t)
        self.assertAlmostEqual(preco_futuro/S0, crescimento_esperado, delta=0.001)
        print(f"\nPreço futuro em 30 dias (z=0): {preco_futuro:.2f} (crescimento de {((preco_futuro/S0)-1)*100:.2f}%)")
    
    def test_preco_futuro_90dias(self):
        # Teste para 90 dias úteis
        S0 = 100.0  # Preço atual
        mu = 0.10   # Retorno médio de 10% ao ano
        sigma = 0.30  # Volatilidade de 30% ao ano
        t = 90/252  # 90 dias úteis
        
        # Usar um valor fixo de z para teste determinístico
        z = 0.0  # Valor médio da normal padrão
        
        preco_futuro = TradeHelper.preco_futuro(S0, mu, sigma, t, z)
        
        # O preço futuro deve ser maior que o preço atual (com z = 0)
        self.assertGreater(preco_futuro, S0)
        
        # Com z = 0, o crescimento deve ser aproximadamente 1.95%
        # Fórmula: exp((mu - 0.5*sigma^2)*t)
        crescimento_esperado = np.exp((mu - 0.5 * sigma**2) * t)
        self.assertAlmostEqual(preco_futuro/S0, crescimento_esperado, delta=0.001)
        print(f"\nPreço futuro em 90 dias (z=0): {preco_futuro:.2f} (crescimento de {((preco_futuro/S0)-1)*100:.2f}%)")
    
    def test_preco_futuro_simulacao_multipla(self):
        # Teste com múltiplas simulações para verificar a distribuição
        S0 = 100.0  # Preço atual
        mu = 0.10   # Retorno médio de 10% ao ano
        sigma = 0.30  # Volatilidade de 30% ao ano
        t = 30/252  # 30 dias úteis
        
        # Fazer 1000 simulações
        n_simulacoes = 1000
        precos_futuros = []
        
        for _ in range(n_simulacoes):
            preco = TradeHelper.preco_futuro(S0, mu, sigma, t)
            precos_futuros.append(preco)
        
        # Calcular estatísticas
        media = np.mean(precos_futuros)
        desvio = np.std(precos_futuros)
        
        # Verificar se a média está próxima do valor esperado
        # Fórmula: S0 * exp(mu * t)
        valor_esperado = S0 * np.exp(mu * t)
        self.assertAlmostEqual(media, valor_esperado, delta=valor_esperado * 0.05)  # 5% de tolerância
        
        # Verificar se o desvio padrão está próximo do valor teórico
        # Fórmula: S0 * exp(mu * t) * sqrt(exp(sigma^2 * t) - 1)
        desvio_teorico = S0 * np.exp(mu * t) * np.sqrt(np.exp(sigma**2 * t) - 1)
        self.assertAlmostEqual(desvio, desvio_teorico, delta=desvio_teorico * 0.1)  # 10% de tolerância
        
        print(f"\nSimulação de {n_simulacoes} cenários:")
        print(f"Média dos preços futuros: {media:.2f}")
        print(f"Desvio padrão: {desvio:.2f}")
        print(f"Valor mínimo: {min(precos_futuros):.2f}")
        print(f"Valor máximo: {max(precos_futuros):.2f}")
    
    def test_preco_futuro_parametros_invalidos(self):
        # Teste com parâmetros inválidos
        with self.assertRaises(ValueError):
            TradeHelper.preco_futuro(100.0, 0.10, 0.30, 0)  # t = 0
        
        with self.assertRaises(ValueError):
            TradeHelper.preco_futuro(100.0, 0.10, 0.30, -1)  # t negativo
    
    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

if __name__ == '__main__':
    unittest.main() 