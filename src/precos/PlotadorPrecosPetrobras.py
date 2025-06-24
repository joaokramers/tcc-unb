import sys
import os

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date
import numpy as np
from helper.TradeHelper import TradeHelper

VOL_DIAS = 252  # Altere aqui para o número de dias desejado para volatilidade

class PlotadorPrecosPetrobras:
    def __init__(self, caminho_banco: str = None):
        """
        Inicializa o plotador de preços da Petrobras.
        
        Args:
            caminho_banco: Caminho para o banco de dados SQLite
        """
        if caminho_banco is None:
            # Usa caminho absoluto baseado no diretório atual
            diretorio_atual = os.path.dirname(os.path.abspath(__file__))
            caminho_banco = os.path.join(diretorio_atual, '..', '..', 'banco', 'mercado_opcoes.db')
        
        self.caminho_banco = caminho_banco
        self.conn = None
        self.dados_petrobras = None
        
    def conectar_banco(self):
        """Conecta ao banco de dados."""
        try:
            self.conn = sqlite3.connect(self.caminho_banco)
            print("Conectado ao banco de dados com sucesso.")
        except Exception as e:
            print(f"Erro ao conectar ao banco: {str(e)}")
            raise
    
    def carregar_dados_petrobras(self, data_inicio: str = '2025-01-01', data_fim: str = None):
        """
        Carrega os dados de preços da Petrobras do banco de dados.
        
        Args:
            data_inicio: Data de início no formato 'YYYY-MM-DD' (padrão: '2025-01-01')
            data_fim: Data de fim no formato 'YYYY-MM-DD' (se None, usa a data atual)
        """
        if self.conn is None:
            self.conectar_banco()
        
        if data_fim is None:
            data_fim = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Busca dados da Petrobras (ID = 1 para PETR4)
            query = """
                SELECT data, abertura, fechamento, maximo, minimo
                FROM HIST_ATIVO
                WHERE id_ativo = 1 
                  AND data >= ?
                  AND data <= ?
                ORDER BY data ASC
            """
            
            df = pd.read_sql_query(query, self.conn, params=[data_inicio, data_fim])
            
            if df.empty:
                print(f"Nenhum dado encontrado para o período {data_inicio} a {data_fim}")
                return None
            
            # Converte a coluna data para datetime
            df['data'] = pd.to_datetime(df['data'])
            
            # Define a data como índice
            df.set_index('data', inplace=True)
            
            self.dados_petrobras = df
            print(f"Carregados {len(df)} registros de preços da Petrobras")
            print(f"Período: {df.index.min().strftime('%d/%m/%Y')} a {df.index.max().strftime('%d/%m/%Y')}")
            
            return df
            
        except Exception as e:
            print(f"Erro ao carregar dados: {str(e)}")
            return None
    
    def plotar_precos_basico(self, titulo: str = "Preços da Petrobras (PETR4) - Real vs Monte Carlo", 
                           tamanho_figura: tuple = (12, 8)):
        """
        Plota um gráfico básico dos preços de fechamento da Petrobras com simulação de Monte Carlo.
        Para cada dia real, simula o preço do dia seguinte 1000 vezes.
        
        Args:
            titulo: Título do gráfico
            tamanho_figura: Tupla com (largura, altura) da figura
        """
        if self.dados_petrobras is None:
            print("Dados não carregados. Execute carregar_dados_petrobras() primeiro.")
            return
        
        # Parâmetros para simulação de Monte Carlo
        n_simulacoes = 1000
        mu = 0.06  # Taxa de retorno anual (6%)
        
        # Simulação de Monte Carlo para cada dia
        print(f"Executando {n_simulacoes} simulações para cada dia...")
        
        precos_reais = self.dados_petrobras['fechamento'].values
        datas = self.dados_petrobras.index
        
        # Arrays para armazenar resultados
        medias_simulacao = [precos_reais[0]]  # Primeiro valor = primeiro preço real
        quantis_025 = [precos_reais[0]]       # Primeiro valor = primeiro preço real
        quantis_975 = [precos_reais[0]]       # Primeiro valor = primeiro preço real
        pontos_dentro_intervalo = 1
        total_pontos = 1
        
        # Para cada dia de 2025 (começando do segundo dia), simula o preço do dia seguinte
        for i in range(1, len(precos_reais)):
            preco_atual = precos_reais[i-1]  # Preço real do dia anterior
            
            # Calcula volatilidade para este dia específico
            try:
                data_atual = datas[i].strftime('%Y-%m-%d')
                sigma_anual = TradeHelper.recuperaVolatilidadeAnualPara_x_Pregoes(
                    self.conn, VOL_DIAS, 'PETR4', data_atual
                )
                sigma = sigma_anual
            except Exception as e:
                print(f"Erro ao calcular volatilidade para dia {i}: {e}")
                sigma = 0.015  # Volatilidade diária padrão de 1.5%
            
            # Simula o preço do dia seguinte 1000 vezes
            precos_simulados = []
            for j in range(n_simulacoes):
                # Simula apenas um passo usando MBG
                trajetoria_um_passo = TradeHelper.rgbm(VOL_DIAS, preco_atual, mu, sigma, seed=i*1000+j, ate_passo=1)
                precos_simulados.append(trajetoria_um_passo[1])  # Pega o segundo valor (após um passo)
            
            # Calcula estatísticas para este dia
            media = np.mean(precos_simulados)
            quantil_025_val = np.quantile(precos_simulados, 0.025)
            quantil_975_val = np.quantile(precos_simulados, 0.975)
            
            medias_simulacao.append(media)
            quantis_025.append(quantil_025_val)
            quantis_975.append(quantil_975_val)
            
            # Verifica se o preço real do dia seguinte está dentro do intervalo (exceto para o último dia)
            if i < len(precos_reais) - 1:
                preco_seguinte_real = precos_reais[i + 1]
                if quantil_025_val <= preco_seguinte_real <= quantil_975_val:
                    pontos_dentro_intervalo += 1
                total_pontos += 1
            
            if i % 20 == 0:  # Progresso a cada 20 dias
                print(f"Processados {i+1}/{len(precos_reais)} dias...")
        
        # Estatísticas de cobertura do intervalo
        cobertura = (pontos_dentro_intervalo / total_pontos) * 100
        print(f"\nDIAGNÓSTICO DO MODELO:")
        print(f"Pontos dentro do intervalo de confiança: {pontos_dentro_intervalo}/{total_pontos} ({cobertura:.1f}%)")
        print(f"Esperado: ~95% dos pontos dentro do intervalo")
        
        if cobertura < 90:
            print("⚠️  AVISO: Cobertura muito baixa! O modelo pode estar subestimando a volatilidade.")
        elif cobertura > 98:
            print("⚠️  AVISO: Cobertura muito alta! O modelo pode estar superestimando a volatilidade.")
        else:
            print("✅ Cobertura adequada do intervalo de confiança.")
        
        # Cria o gráfico
        plt.figure(figsize=tamanho_figura)
        
        # Usa todas as datas e preços (agora temos simulação para todos os dias)
        datas_plot = datas[:-1]  # Remove o último dia
        precos_reais_plot = precos_reais[:-1]  # Remove o último dia
        quantis_025_plot = quantis_025[:-1]
        quantis_975_plot = quantis_975[:-1]
        medias_simulacao_plot = medias_simulacao[:-1]
        
        # Plota dados reais
        plt.plot(datas_plot, precos_reais_plot, 
                linewidth=2, color='blue', label='Preço Real', zorder=3)
        plt.scatter(datas_plot, precos_reais_plot, 
                   color='blue', s=30, zorder=5, alpha=0.7, edgecolors='darkblue', linewidth=1)
        
        # Plota intervalo de confiança 95%
        plt.fill_between(datas_plot, quantis_025_plot, quantis_975_plot, 
                        alpha=0.3, color='red', label='Intervalo de Confiança 95%', zorder=1)
        
        # Plota média da simulação (mesmo número de pontos que a Petrobras)
        plt.plot(datas_plot, medias_simulacao_plot, 
                linewidth=2, color='red', linestyle='--', label='Média Monte Carlo (dia seguinte)', zorder=2)
        
        # Configurações do gráfico
        plt.title(titulo, fontsize=16, fontweight='bold')
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Preço (R$)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Formatação do eixo X (datas)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Adiciona informações da simulação
        preco_final_real = precos_reais[-1]
        preco_inicial = precos_reais[0]
        variacao_real = ((preco_final_real - preco_inicial) / preco_inicial) * 100
        
        # Estatísticas do último dia simulado
        if medias_simulacao:
            preco_final_sim = medias_simulacao[-1]
            variacao_sim = ((preco_final_sim - preco_inicial) / preco_inicial) * 100
            intervalo_final = quantis_975[-1] - quantis_025[-1]
        else:
            preco_final_sim = preco_final_real
            variacao_sim = variacao_real
            intervalo_final = 0
        
        texto_info = (
            f"Preço inicial: R$ {preco_inicial:.2f}\n"
            f"Preço final real: R$ {preco_final_real:.2f} ({variacao_real:+.2f}%)\n"
            f"Preço final simulado: R$ {preco_final_sim:.2f} ({variacao_sim:+.2f}%)\n"
            f"Volatilidade usada ({VOL_DIAS} dias, anualizada): {sigma:.1%}\n"
            f"Simulações por dia: {n_simulacoes}"
        )
        
        plt.text(0.02, 0.98, texto_info,
                transform=plt.gca().transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox=dict(facecolor='white', edgecolor='gray', alpha=0.8))
        
        plt.tight_layout()
        plt.show()
        
        # Retorna estatísticas da simulação
        return {
            'preco_inicial': preco_inicial,
            'preco_final_real': preco_final_real,
            'preco_final_simulado': preco_final_sim,
            'variacao_real': variacao_real,
            'variacao_simulada': variacao_sim,
            'volatilidade_usada': sigma,
            'n_simulacoes': n_simulacoes,
            'medias_simulacao': medias_simulacao,
            'quantil_025': quantis_025,
            'quantil_975': quantis_975,
            'intervalo_final': intervalo_final
        }
    
    def calcular_estatisticas(self):
        """
        Calcula e exibe estatísticas dos preços da Petrobras.
        
        Returns:
            dict: Dicionário com as estatísticas calculadas
        """
        if self.dados_petrobras is None:
            print("Dados não carregados. Execute carregar_dados_petrobras() primeiro.")
            return None
        
        precos = self.dados_petrobras['fechamento']
        
        estatisticas = {
            'preco_atual': precos.iloc[-1],
            'preco_inicial': precos.iloc[0],
            'variacao_percentual': ((precos.iloc[-1] - precos.iloc[0]) / precos.iloc[0]) * 100,
            'preco_medio': precos.mean(),
            'preco_mediano': precos.median(),
            'preco_maximo': precos.max(),
            'preco_minimo': precos.min(),
            'desvio_padrao': precos.std(),
            'volatilidade_anual': precos.std() * np.sqrt(252),
            'dias_negociados': len(precos)
        }
        
        print("\n" + "="*50)
        print("ESTATÍSTICAS DA PETROBRAS")
        print("="*50)
        print(f"Preço atual: R$ {estatisticas['preco_atual']:.2f}")
        print(f"Preço inicial: R$ {estatisticas['preco_inicial']:.2f}")
        print(f"Variação percentual: {estatisticas['variacao_percentual']:.2f}%")
        print(f"Preço médio: R$ {estatisticas['preco_medio']:.2f}")
        print(f"Preço mediano: R$ {estatisticas['preco_mediano']:.2f}")
        print(f"Preço máximo: R$ {estatisticas['preco_maximo']:.2f}")
        print(f"Preço mínimo: R$ {estatisticas['preco_minimo']:.2f}")
        print(f"Desvio padrão: R$ {estatisticas['desvio_padrao']:.2f}")
        print(f"Volatilidade anual: {estatisticas['volatilidade_anual']:.2f}")
        print(f"Dias negociados: {estatisticas['dias_negociados']}")
        print("="*50)
        
        return estatisticas
    
    def fechar_conexao(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            print("Conexão com o banco de dados fechada.")


def main():
    """
    Função principal para demonstrar o uso da classe.
    """
    # Cria instância do plotador
    plotador = PlotadorPrecosPetrobras()
    
    try:
        # Carrega dados desde janeiro de 2025
        dados = plotador.carregar_dados_petrobras('2025-01-01')
        
        if dados is not None:
            # Calcula estatísticas
            estatisticas = plotador.calcular_estatisticas()
            
            # Plota apenas o gráfico básico
            plotador.plotar_precos_basico()
            
    except Exception as e:
        print(f"Erro durante a execução: {str(e)}")
    
    finally:
        # Fecha a conexão
        plotador.fechar_conexao()


if __name__ == "__main__":
    main() 