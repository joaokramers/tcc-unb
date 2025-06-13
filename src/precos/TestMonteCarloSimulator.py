import sys
import os

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import unittest
import numpy as np
from datetime import datetime
from MonteCarloSimulator import MonteCarloSimulator
from helper.TradeHelper import TradeHelper

class TestMonteCarloSimulator(unittest.TestCase):
    
    def setUp(self):
        # Configuração comum para os testes
        self.S0 = 100.0  # Preço inicial
        self.mu = 0.10   # Retorno médio anual de 10%
        self.sigma = 0.30  # Volatilidade anual de 30%
        self.simulador = MonteCarloSimulator(self.S0, self.mu, self.sigma)
    
    def test_inicializacao(self):
        # Testa se o simulador é inicializado corretamente
        self.assertEqual(self.simulador.S0, 100.0)
        self.assertEqual(self.simulador.mu, 0.10)
        self.assertEqual(self.simulador.sigma, 0.30)
        self.assertEqual(self.simulador.dias_uteis_por_ano, 252)
        
        # Testa com dias úteis personalizados
        simulador_custom = MonteCarloSimulator(self.S0, self.mu, self.sigma, 260)
        self.assertEqual(simulador_custom.dias_uteis_por_ano, 260)
    
    def test_simular_trajetoria_unica(self):
        # Testa a simulação de uma única trajetória
        dias = 30
        trajetoria = self.simulador.simular_trajetoria_bs(dias, seed=42)
        
        # Verifica o tamanho da trajetória
        self.assertEqual(len(trajetoria), dias + 1)
        
        # Verifica se o primeiro preço é o preço inicial
        self.assertEqual(trajetoria[0], self.S0)
        
        # Verifica se todos os preços são positivos
        for preco in trajetoria:
            self.assertGreater(preco, 0)
    
    def test_simular_multiplas_trajetorias(self):
        # Testa a simulação de múltiplas trajetórias
        dias = 30
        n_simulacoes = 100
        trajetorias = self.simulador.simular_multiplas_trajetorias(dias, n_simulacoes, seed=42)
        
        # Verifica as dimensões da matriz de trajetórias
        self.assertEqual(trajetorias.shape, (n_simulacoes, dias + 1))
        
        # Verifica se a primeira coluna é o preço inicial
        for i in range(n_simulacoes):
            self.assertEqual(trajetorias[i, 0], self.S0)
    
    def test_calcular_estatisticas(self):
        # Testa o cálculo de estatísticas
        dias = 30
        n_simulacoes = 1000
        trajetorias = self.simulador.simular_multiplas_trajetorias(dias, n_simulacoes, seed=42)
        
        estatisticas = self.simulador.calcular_estatisticas(trajetorias)
        
        # Verifica se todas as estatísticas foram calculadas
        self.assertIn('media', estatisticas)
        self.assertIn('desvio', estatisticas)
        self.assertIn('minimo', estatisticas)
        self.assertIn('maximo', estatisticas)
        
        # Verifica o tamanho dos arrays de estatísticas
        self.assertEqual(len(estatisticas['media']), dias + 1)
        self.assertEqual(len(estatisticas['desvio']), dias + 1)
        self.assertEqual(len(estatisticas['minimo']), dias + 1)
        self.assertEqual(len(estatisticas['maximo']), dias + 1)
        
        # Verifica se a média inicial é o preço inicial
        self.assertEqual(estatisticas['media'][0], self.S0)
        
        # Verifica se o desvio inicial é zero
        self.assertEqual(estatisticas['desvio'][0], 0)
        
        # Verifica se o mínimo e máximo iniciais são o preço inicial
        self.assertEqual(estatisticas['minimo'][0], self.S0)
        self.assertEqual(estatisticas['maximo'][0], self.S0)
        
        # Verifica se o preço médio final está dentro de um intervalo razoável
        # Para mu = 0.10, sigma = 0.30, e 30 dias, o preço médio deve estar próximo de:
        # S0 * exp(mu * (30/252)) = 100 * exp(0.10 * (30/252)) ≈ 101.2
        preco_medio_esperado = self.S0 * np.exp(self.mu * (dias / 252))
        self.assertAlmostEqual(estatisticas['media'][-1], preco_medio_esperado, delta=10.0)
    
    def test_consistencia_com_preco_futuro(self):
        # Testa se a simulação é consistente com o método preco_futuro do TradeHelper
        dias = 1
        dt = 1 / 252  # Um dia útil
        
        # Simula um único dia com z fixo
        z = 1.0
        preco_esperado = TradeHelper.preco_futuro(self.S0, self.mu, self.sigma, dt, z=z)
        
        # Modifica temporariamente o método random.normal para retornar z fixo
        original_normal = np.random.normal
        np.random.normal = lambda: z
        
        try:
            trajetoria = self.simulador.simular_trajetoria_bs(dias)
            self.assertAlmostEqual(trajetoria[1], preco_esperado, places=6)
        finally:
            # Restaura o método original
            np.random.normal = original_normal

if __name__ == '__main__':
    unittest.main() 