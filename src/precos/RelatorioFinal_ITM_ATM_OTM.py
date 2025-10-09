#!/usr/bin/env python3
"""
Gera relatório final consolidado das análises ITM, ATM e OTM.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
import pandas as pd
from precos.ComparadorPrecosOpcoes import ComparadorPrecosOpcoes
from helper.TradeHelper import TradeHelper

# Lista de opções
# Classificação baseada no DELTA inicial (critério oficial):
# - Delta 0,00-0,30: OTM (Out of The Money)
# - Delta 0,31-0,70: ATM (At The Money)
# - Delta 0,71-1,00: ITM (In The Money)
#
# Deltas calculados com 30 pregões de volatilidade:
# - PETRI28: Delta = 0.8163 → ITM (In The Money)
# - PETRI313: Delta = 0.6518 → ATM (At The Money)
# - PETRH369: Delta = 0.0490 → OTM (Out of The Money)
OPCOES_ANALISAR = [
    {'ticker': 'PETRI28', 'id_simulacao': 29, 'classificacao': 'ITM'},
    {'ticker': 'PETRI313', 'id_simulacao': 31, 'classificacao': 'ATM'},
    {'ticker': 'PETRH369', 'id_simulacao': 27, 'classificacao': 'OTM'}
]

PREGOES_VOLATILIDADE = [30, 60, 120, 252]

def main():
    caminho_banco = 'banco/mercado_opcoes.db'
    conn = sqlite3.connect(caminho_banco)
    
    print("\n" + "="*80)
    print("RELATÓRIO CONSOLIDADO: ANÁLISE ITM, ATM E OTM")
    print("Comparação de Preços de Mercado vs Black-Scholes")
    print("="*80)
    
    try:
        todos_resultados = []
        
        for opcao_config in OPCOES_ANALISAR:
            ticker = opcao_config['ticker']
            id_sim = opcao_config['id_simulacao']
            classificacao = opcao_config['classificacao']
            
            print(f"\n{'#'*80}")
            print(f"# OPÇÃO: {ticker} ({classificacao})")
            print(f"{'#'*80}\n")
            
            # Recupera informações da opção
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.data_inicio, s.data_termino, o.strike, o.vencimento, a.ticker
                FROM SIMULACAO s
                JOIN OPCAO o ON s.id_opcao = o.id
                JOIN ATIVO a ON o.id_ativo = a.id
                WHERE s.id = ?
            """, (id_sim,))
            
            info = cursor.fetchone()
            data_inicio, data_termino, strike, vencimento, ticker_ativo = info
            
            # Recupera preço inicial
            cursor.execute("""
                SELECT h.abertura
                FROM HIST_ATIVO h
                JOIN ATIVO a ON h.id_ativo = a.id
                WHERE a.ticker = ? AND h.data = ?
            """, (ticker_ativo, data_inicio))
            
            preco_inicial = cursor.fetchone()[0]
            moneyness = (preco_inicial / strike - 1) * 100
            
            print(f"Informações Básicas:")
            print(f"  Ticker: {ticker}")
            print(f"  Strike: R$ {strike:.2f}")
            print(f"  Vencimento: {vencimento}")
            print(f"  Período: {data_inicio} até {data_termino}")
            print(f"  Preço Inicial {ticker_ativo}: R$ {preco_inicial:.2f}")
            print(f"  Moneyness: {moneyness:+.2f}% ({classificacao})")
            
            print(f"\nResultados por Período de Volatilidade:\n")
            print(f"{'Pregões':<10} {'Vol.':<8} {'Dif.Média':<12} {'Dif.Mín.':<12} {'Dif.Máx.':<12} {'Desv.Pad.':<10}")
            print("-"*80)
            
            for pregoes in PREGOES_VOLATILIDADE:
                comparador = ComparadorPrecosOpcoes(
                    conn=conn,
                    id_simulacao=id_sim,
                    pregoes_volatilidade=pregoes,
                    taxa_juros=0.15
                )
                
                comparador.processar()
                df = comparador.listar_dados()
                diferencas = df['Diferença %'].str.rstrip('%').astype(float)
                
                sigma = TradeHelper.recuperaVolatilidadeAnualPara_x_Pregoes(
                    conn, pregoes, ticker_ativo, data_inicio
                )
                
                # Para opções muito OTM, limita os valores extremos para visualização
                dif_media = diferencas.mean()
                dif_min = diferencas.min()
                dif_max = diferencas.max()
                desv_pad = diferencas.std()
                
                # Formata valores absurdos
                def formatar_valor(val):
                    if abs(val) > 1000000:
                        return f"{val:.2e}%"
                    else:
                        return f"{val:+.2f}%"
                
                print(f"{pregoes:<10} {sigma*100:>6.1f}% {formatar_valor(dif_media):<12} {formatar_valor(dif_min):<12} {formatar_valor(dif_max):<12} {formatar_valor(desv_pad):<10}")
                
                todos_resultados.append({
                    'Opção': ticker,
                    'Classificação': classificacao,
                    'Strike': strike,
                    'Preço Inicial': preco_inicial,
                    'Moneyness': f"{moneyness:+.2f}%",
                    'Pregões': pregoes,
                    'Volatilidade': f"{sigma*100:.1f}%",
                    'Dif_Media_%': dif_media,
                    'Dif_Min_%': dif_min,
                    'Dif_Max_%': dif_max,
                    'Desv_Pad_%': desv_pad
                })
            
            # Identifica o melhor
            df_opcao = pd.DataFrame([r for r in todos_resultados if r['Opção'] == ticker])
            idx_melhor = df_opcao['Dif_Media_%'].abs().idxmin()
            melhor = df_opcao.loc[idx_melhor]
            
            print(f"\n✓ Melhor ajuste: {int(melhor['Pregões'])} pregões")
            print(f"  Volatilidade: {melhor['Volatilidade']}")
            print(f"  Diferença Média: {melhor['Dif_Media_%']:+.2f}%")
        
        # Resumo comparativo final
        print(f"\n\n{'='*80}")
        print("RESUMO COMPARATIVO FINAL")
        print(f"{'='*80}\n")
        
        df_todos = pd.DataFrame(todos_resultados)
        
        # Agrupa por opção e pega o melhor de cada
        resumo_final = []
        for classificacao in ['ITM', 'ATM', 'OTM']:
            df_classe = df_todos[df_todos['Classificação'] == classificacao]
            if df_classe.empty:
                continue
            idx_melhor = df_classe['Dif_Media_%'].abs().idxmin()
            melhor = df_classe.loc[idx_melhor]
            
            resumo_final.append({
                'Opção': melhor['Opção'],
                'Classificação': classificacao,
                'Strike': f"R$ {melhor['Strike']:.2f}",
                'Moneyness': melhor['Moneyness'],
                'Melhor Período': f"{int(melhor['Pregões'])} pregões",
                'Volatilidade': melhor['Volatilidade'],
                'Diferença Média': f"{melhor['Dif_Media_%']:+.2f}%"
            })
        
        df_resumo = pd.DataFrame(resumo_final)
        print(df_resumo.to_string(index=False))
        
        print(f"\n{'='*80}")
        print("INSIGHTS E CONCLUSÕES")
        print(f"{'='*80}\n")
        
        print("CRITÉRIO DE CLASSIFICAÇÃO (baseado no Delta):")
        print("  • OTM: Delta entre 0,00 e 0,30")
        print("  • ATM: Delta entre 0,31 e 0,70")
        print("  • ITM: Delta entre 0,71 e 1,00\n")
        
        print("-"*80 + "\n")
        
        print("1. OPÇÃO ITM (In The Money) - PETRI28:")
        print("   • Strike: R$ 28.22 | Preço Inicial PETR4: R$ 29.53 | Moneyness: +4.64%")
        print("   • Delta inicial: 0.8163 → ITM (0,71-1,00)")
        print("   • Alta sensibilidade ao ativo: cada R$ 1,00 no ativo → ~R$ 0,82 na opção")
        print("   • Mercado consistentemente ABAIXO do modelo BS")
        print("   • Possível desconto de liquidez ou preferência do mercado por strikes ATM\n")
        
        print("2. OPÇÃO ATM (At The Money) - PETRI313:")
        print("   • Strike: R$ 29.22 | Preço Inicial PETR4: R$ 29.53 | Moneyness: +1.06%")
        print("   • Delta inicial: 0.6518 → ATM (0,31-0,70)")
        print("   • Sensibilidade moderada: cada R$ 1,00 no ativo → ~R$ 0,65 na opção")
        print("   • Delta no meio da faixa ATM, ideal para análise de eficiência de mercado")
        print("   • Representa o equilíbrio entre valor intrínseco e valor temporal\n")
        
        print("3. OPÇÃO OTM (Out of The Money) - PETRH369:")
        print("   • Strike: R$ 36.23 | Preço Inicial PETR4: R$ 31.52 | Moneyness: -13.00%")
        print("   • Delta inicial: 0.0490 → OTM (0,00-0,30)")
        print("   • Sensibilidade mínima: cada R$ 1,00 no ativo → ~R$ 0,05 na opção")
        print("   • Preços teóricos de BS extremamente baixos (próximos a zero)")
        print("   • Mercado mantém prêmio mínimo pela possibilidade remota de exercício")
        print("   • Diferenças percentuais astronômicas devido a divisão por valores ~zero")
        print("   • LIMITAÇÃO DO MODELO BS para opções profundamente OTM próximas ao vencimento")
        print("   • Mercado precifica 'valor de loteria' não capturado pelo modelo teórico\n")
        
        print(f"{'='*80}\n")
        
        # Salva resumo
        output_file = 'dados-comparacao-preco/relatorio_final_ITM_ATM_OTM.csv'
        os.makedirs('dados-comparacao-preco', exist_ok=True)
        df_resumo.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Relatório salvo em: {output_file}\n")
        
    except Exception as e:
        print(f"\nErro: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()

