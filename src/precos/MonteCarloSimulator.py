import sys
import os

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from helper.TradeHelper import TradeHelper


class MonteCarloSimulator:
    def __init__(self, S0: float, mu: float, sigma: float, dias_uteis_por_ano: int = 252):
        self.S0 = S0
        self.mu = mu
        self.sigma = sigma
        self.dias_uteis_por_ano = dias_uteis_por_ano

    def simular_trajetoria_bs(self, pregoes: int, seed: int = None) -> list:
        if seed is not None:
            np.random.seed(seed)

        precos = [self.S0]
        preco_atual = self.S0
        for _ in range(pregoes):
            dt = 1 / self.dias_uteis_por_ano
            preco_atual = TradeHelper.preco_futuro(preco_atual, self.mu, self.sigma, 1/pregoes)
            precos.append(preco_atual)

        return precos
        #return TradeHelper.preco_futuro(preco_atual, self.mu, self.sigma, pregoes/self.dias_uteis_por_ano)    

    def simular_trajetoria_mbg(self, pregoes: int, seed: int = None) -> list:
        n = pregoes
        return TradeHelper.rgbm(n, self.S0, self.mu, self.sigma, seed, ate_passo=n)

    def simular_multiplas_trajetorias(self, pregoes: int, n_simulacoes: int, seed: int = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)

        precos = np.zeros((n_simulacoes, pregoes + 1))
        precos[:, 0] = self.S0
        for i in range(n_simulacoes):
            precos[i, 1:] = self.simular_trajetoria_mbg(pregoes)[1:]
            #precos[i, 1:] = self.simular_trajetoria_bs(pregoes)[1:]


        return precos

    def calcular_estatisticas(self, trajetorias: np.ndarray) -> dict:
        media = np.mean(trajetorias, axis=0)
        desvio = np.std(trajetorias, axis=0)
        minimo = np.min(trajetorias, axis=0)
        maximo = np.max(trajetorias, axis=0)
        return {
            'media': media,
            'desvio': desvio,
            'minimo': minimo,
            'maximo': maximo
        }

    def plotar_trajetorias(
        self,
        trajetorias: np.ndarray,
        titulo: str = "Simulação de Monte Carlo",
        data_inicial: datetime = None,
        max_trajetorias: int = 100,
        preco_inicial_real: float = None,
        preco_final_real: float = None,
        datas_reais: list = None,
        precos_reais: list = None
    ):
        n_simulacoes, n_dias = trajetorias.shape
        n_plot = min(n_simulacoes, max_trajetorias)
        indices = np.random.choice(n_simulacoes, n_plot, replace=False)

        plt.figure(figsize=(12, 6))

        x_vals = range(n_dias)
        plt.xlabel('Dias úteis')

        for i in indices:
            plt.plot(x_vals, trajetorias[i], alpha=0.3, linewidth=0.8)

        estatisticas = self.calcular_estatisticas(trajetorias)
        plt.plot(x_vals, estatisticas['media'], 'r-', linewidth=2, label='Média')

        plt.fill_between(
            x_vals,
            estatisticas['media'] - 1.96 * estatisticas['desvio'],
            estatisticas['media'] + 1.96 * estatisticas['desvio'],
            color='r', alpha=0.1, label='Intervalo de confiança de 95%'
        )

        plt.title(titulo)
        plt.ylabel('Preço')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()

        preco_bs = 0
        for i in range(1000):
            preco_bs+=TradeHelper.preco_futuro(self.S0, self.mu, self.sigma, n_dias/self.dias_uteis_por_ano)
        preco_bs/=1000

        if preco_inicial_real is not None and preco_final_real is not None:
            texto_info = (
                f"Preço inicial real: R$ {preco_inicial_real:.2f}\n"
                f"Preço final real: R$ {preco_final_real:.2f}\n"
                f"Preço final médio MBG: R$ {estatisticas['media'][-1]:.2f}\n"
                f"Preço final médio BS: R$ {preco_bs:.2f}"
               )
            plt.text(
                0.01, 0.02, texto_info,
                transform=plt.gca().transAxes,
                fontsize=10,
                verticalalignment='bottom',
                bbox=dict(facecolor='white', edgecolor='gray', alpha=0.7)
            )

        if datas_reais is not None and precos_reais is not None:
            plt.plot(
                x_vals,
                precos_reais,
                color='black',
                linewidth=2.0,
                linestyle='--',
                label='Trajetória real'
            )

        plt.show()


if __name__ == "__main__":
    caminho_banco = 'banco/mercado_opcoes.db'
    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()

    # 1. Busca a opção
    cursor.execute("SELECT id, id_ativo, vencimento FROM OPCAO WHERE ticker = 'PETRE301'")
    opcao = cursor.fetchone()
    if not opcao:
        raise ValueError("Opção PETRE301 não encontrada.")
    id_opcao, id_ativo, data_vencimento = opcao
    data_vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()

    # 2. Busca os últimos x pregões antes do vencimento
    pregoes = 20
    cursor.execute("""
        SELECT DISTINCT data
        FROM HIST_ATIVO
        WHERE id_ativo = ?
          AND data <= ?
        ORDER BY data DESC
        LIMIT ?
    """, (id_ativo, data_vencimento, pregoes+1))
    datas = cursor.fetchall()

    
    if len(datas) < pregoes+1:
        raise ValueError(f"Menos de {pregoes} pregões antes do vencimento.")
    datas = sorted([datetime.strptime(row[0], "%Y-%m-%d").date() for row in datas])
    data_inicial = datas[0]

    # 3. Busca preço inicial
    cursor.execute("""
        SELECT abertura
        FROM HIST_ATIVO
        WHERE id_ativo = ?
          AND data = ?
    """, (id_ativo, data_inicial))
    preco_inicial = cursor.fetchone()
    if not preco_inicial:
        raise ValueError("Preço inicial não encontrado.")
    S0 = preco_inicial[0]

    # 4. Busca preço final
    cursor.execute("""
        SELECT fechamento
        FROM HIST_ATIVO
        WHERE id_ativo = ?
          AND data = ?
    """, (id_ativo, data_vencimento))
    preco_final = cursor.fetchone()
    if not preco_final:
        raise ValueError("Preço final não encontrado.")
    S_t = preco_final[0]

    # 5. Parâmetros do modelo
    mu = 0.06
    #sigma = TradeHelper.recuperaVolatilidadeAnual(conn, 'PETR4', data_inicial.strftime('%Y-%m-%d'))
    pregoes_volatilidade = 252
    sigma = TradeHelper.recuperaVolatilidadeAnualPara_x_Pregoes(conn, pregoes_volatilidade, 'PETR4', data_inicial.strftime('%Y-%m-%d'))

    # 6. Simulação
    simulador = MonteCarloSimulator(S0, mu, sigma)
    trajetorias = simulador.simular_multiplas_trajetorias(pregoes, 1000)

    # 7. Trajetória real no intervalo
    cursor.execute("""
        SELECT data, fechamento
        FROM HIST_ATIVO
        WHERE id_ativo = ?
          AND data IN ({seq})
        ORDER BY data ASC
    """.format(seq=",".join(["?"] * len(datas))), [id_ativo] + [d.strftime('%Y-%m-%d') for d in datas])
    trajetoria_real = cursor.fetchall()
    datas_reais = [datetime.strptime(row[0], '%Y-%m-%d') for row in trajetoria_real]

    precos_reais = [row[1] for row in trajetoria_real]
    precos_reais[0] = S0


    # 8. Título e plot
    titulo = (
        f"Simulação de Monte Carlo de {data_inicial.strftime('%d/%m/%Y')} "
        f"até {data_vencimento.strftime('%d/%m/%Y')} ({pregoes} pregões) - "
        f"Volatilidade: {sigma * 100:.1f}% (base {pregoes_volatilidade} pregões), "
        f"Juros: {mu * 100:.1f}%"
    )

    simulador.plotar_trajetorias(
        trajetorias,
        titulo,
        data_inicial,
        preco_inicial_real=S0,
        preco_final_real=S_t,
        datas_reais=datas_reais,
        precos_reais=precos_reais
    )
