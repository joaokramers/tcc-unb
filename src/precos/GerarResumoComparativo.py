#!/usr/bin/env python3
"""
Gera um resumo comparativo dos resultados para diferentes períodos de volatilidade.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
import pandas as pd
from precos.ComparadorPrecosOpcoes import ComparadorPrecosOpcoes

# ID da simulação a ser analisada
ID_SIMULACAO = 32

def gerar_resumo_comparativo(conn, id_simulacao):
    """
    Gera um resumo comparativo para diferentes períodos de volatilidade.
    """
    # Lista de pregões de volatilidade
    pregoes_lista = [30, 60, 120, 252]
    
    # Armazena resultados
    resumo_dados = []
    
    print("\n" + "="*80)
    print("RESUMO COMPARATIVO - IMPACTO DO PERÍODO DE VOLATILIDADE")
    print("="*80)
    
    for pregoes in pregoes_lista:
        # Cria o comparador
        comparador = ComparadorPrecosOpcoes(
            conn=conn,
            id_simulacao=id_simulacao,
            pregoes_volatilidade=pregoes,
            taxa_juros=0.15
        )
        
        # Processa os dados
        comparador.processar()
        
        # Calcula estatísticas
        df = comparador.listar_dados()
        diferencas = df['Diferença %'].str.rstrip('%').astype(float)
        
        # Recupera a volatilidade inicial
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ticker, strike, vencimento
            FROM OPCAO
            WHERE id = ?
        """, (comparador.id_opcao,))
        
        opcao = cursor.fetchone()
        ticker = opcao[0]
        
        from helper.TradeHelper import TradeHelper
        sigma = TradeHelper.recuperaVolatilidadeAnualPara_x_Pregoes(
            conn,
            pregoes,
            comparador.ticker_ativo,
            comparador.data_inicio.strftime("%Y-%m-%d")
        )
        
        # Armazena os dados
        resumo_dados.append({
            'Pregões Vol.': pregoes,
            'Volatilidade': f"{sigma*100:.1f}%",
            'Diferença Média': f"{diferencas.mean():.2f}%",
            'Diferença Mín.': f"{diferencas.min():.2f}%",
            'Diferença Máx.': f"{diferencas.max():.2f}%",
            'Desvio Padrão': f"{diferencas.std():.2f}%",
            'Dias Analisados': len(df)
        })
    
    # Cria DataFrame do resumo
    df_resumo = pd.DataFrame(resumo_dados)
    
    # Imprime o resumo
    print(f"\nOpção: {ticker}")
    print(f"Simulação ID: {id_simulacao}")
    print(f"Período: {comparador.data_inicio} até {comparador.data_termino}")
    print("\n" + "-"*80)
    print(df_resumo.to_string(index=False))
    print("-"*80)
    
    # Análise e insights
    print("\n📊 INSIGHTS:")
    print("-"*80)
    
    volatilidades = [float(d['Volatilidade'].rstrip('%')) for d in resumo_dados]
    diferencas_medias = [float(d['Diferença Média'].rstrip('%')) for d in resumo_dados]
    
    idx_melhor = min(range(len(diferencas_medias)), key=lambda i: abs(diferencas_medias[i]))
    
    print(f"✓ Melhor ajuste (menor diferença absoluta): {resumo_dados[idx_melhor]['Pregões Vol.']} pregões")
    print(f"  • Volatilidade: {resumo_dados[idx_melhor]['Volatilidade']}")
    print(f"  • Diferença Média: {resumo_dados[idx_melhor]['Diferença Média']}")
    
    print(f"\n✓ Volatilidade mais baixa: {min(volatilidades):.1f}% ({resumo_dados[volatilidades.index(min(volatilidades))]['Pregões Vol.']} pregões)")
    print(f"✓ Volatilidade mais alta: {max(volatilidades):.1f}% ({resumo_dados[volatilidades.index(max(volatilidades))]['Pregões Vol.']} pregões)")
    
    print(f"\n✓ Tendência observada:")
    if all(d < 0 for d in diferencas_medias):
        print("  • Mercado consistentemente ABAIXO do modelo Black-Scholes")
    elif all(d > 0 for d in diferencas_medias):
        print("  • Mercado consistentemente ACIMA do modelo Black-Scholes")
    else:
        print("  • Mercado varia entre ACIMA e ABAIXO do modelo Black-Scholes")
    
    print("="*80 + "\n")
    
    return df_resumo

if __name__ == "__main__":
    # Conecta ao banco de dados
    caminho_banco = 'banco/mercado_opcoes.db'
    conn = sqlite3.connect(caminho_banco)
    
    try:
        # Gera o resumo comparativo
        df_resumo = gerar_resumo_comparativo(conn, ID_SIMULACAO)
        
        # Salva em arquivo CSV
        output_file = f'dados-comparacao-preco/resumo_comparativo_simulacao_{ID_SIMULACAO}.csv'
        os.makedirs('dados-comparacao-preco', exist_ok=True)
        df_resumo.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Resumo salvo em: {output_file}")
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

