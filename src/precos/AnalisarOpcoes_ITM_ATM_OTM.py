#!/usr/bin/env python3
"""
Analisa e compara opções ITM, ATM e OTM para diferentes períodos de volatilidade.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime
import pandas as pd
from precos.ComparadorPrecosOpcoes import ComparadorPrecosOpcoes
from helper.TradeHelper import TradeHelper

# Lista de opções a serem analisadas
# Formato: (Nome, Ticker, ID_Simulação, Classificação)
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
    {
        'nome': 'PETRI28 (ITM - In The Money)',
        'ticker': 'PETRI28',
        'id_simulacao': 29,
        'classificacao': 'ITM'
    },
    {
        'nome': 'PETRI313 (ATM - At The Money)',
        'ticker': 'PETRI313',
        'id_simulacao': 31,
        'classificacao': 'ATM'
    },
    {
        'nome': 'PETRH369 (OTM - Out of The Money)',
        'ticker': 'PETRH369',
        'id_simulacao': 27,
        'classificacao': 'OTM'
    }
]

# Períodos de volatilidade a serem testados
PREGOES_VOLATILIDADE = [30, 60, 120, 252]

def analisar_opcao(conn, opcao_config):
    """
    Analisa uma opção para todos os períodos de volatilidade.
    """
    id_simulacao = opcao_config['id_simulacao']
    nome = opcao_config['nome']
    classificacao = opcao_config['classificacao']
    
    print("\n" + "="*80)
    print(f"ANÁLISE: {nome}")
    print("="*80)
    
    # Armazena resultados
    resumo_dados = []
    
    # Recupera informações básicas da simulação
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.data_inicio, s.data_termino, o.ticker, o.strike, o.vencimento, a.ticker
        FROM SIMULACAO s
        JOIN OPCAO o ON s.id_opcao = o.id
        JOIN ATIVO a ON o.id_ativo = a.id
        WHERE s.id = ?
    """, (id_simulacao,))
    
    info = cursor.fetchone()
    data_inicio = info[0]
    data_termino = info[1]
    ticker_opcao = info[2]
    strike = info[3]
    vencimento = info[4]
    ticker_ativo = info[5]
    
    print(f"\nInformações da Opção:")
    print(f"  Ticker: {ticker_opcao}")
    print(f"  Strike: R$ {strike:.2f}")
    print(f"  Vencimento: {vencimento}")
    print(f"  Período: {data_inicio} até {data_termino}")
    print(f"  Ativo: {ticker_ativo}")
    
    # Recupera o preço do ativo no início da simulação
    cursor.execute("""
        SELECT h.abertura
        FROM HIST_ATIVO h
        JOIN ATIVO a ON h.id_ativo = a.id
        WHERE a.ticker = ? AND h.data = ?
    """, (ticker_ativo, data_inicio))
    
    preco_inicial = cursor.fetchone()
    if preco_inicial:
        preco_inicial = preco_inicial[0]
        print(f"  Preço Inicial {ticker_ativo}: R$ {preco_inicial:.2f}")
        moneyness = (preco_inicial / strike - 1) * 100
        print(f"  Moneyness: {moneyness:+.2f}% ({classificacao})")
    
    print("\n" + "-"*80)
    
    # Analisa para cada período de volatilidade
    for pregoes in PREGOES_VOLATILIDADE:
        try:
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
            
            # Recupera a volatilidade
            sigma = TradeHelper.recuperaVolatilidadeAnualPara_x_Pregoes(
                conn,
                pregoes,
                ticker_ativo,
                data_inicio
            )
            
            # Armazena os dados
            resumo_dados.append({
                'Pregões Vol.': pregoes,
                'Volatilidade': f"{sigma*100:.1f}%",
                'Diferença Média': f"{diferencas.mean():.2f}%",
                'Diferença Mín.': f"{diferencas.min():.2f}%",
                'Diferença Máx.': f"{diferencas.max():.2f}%",
                'Desvio Padrão': f"{diferencas.std():.2f}%",
                'Dias': len(df)
            })
            
        except Exception as e:
            print(f"  ⚠ Erro ao processar {pregoes} pregões: {str(e)}")
    
    # Cria DataFrame do resumo
    if resumo_dados:
        df_resumo = pd.DataFrame(resumo_dados)
        
        print("\nRESUMO COMPARATIVO:")
        print(df_resumo.to_string(index=False))
        print("-"*80)
        
        # Identifica o melhor período
        diferencas_medias = [float(d['Diferença Média'].rstrip('%')) for d in resumo_dados]
        idx_melhor = min(range(len(diferencas_medias)), key=lambda i: abs(diferencas_medias[i]))
        
        print(f"\n✓ Melhor ajuste: {resumo_dados[idx_melhor]['Pregões Vol.']} pregões")
        print(f"  • Volatilidade: {resumo_dados[idx_melhor]['Volatilidade']}")
        print(f"  • Diferença Média: {resumo_dados[idx_melhor]['Diferença Média']}")
        
        return {
            'opcao': nome,
            'classificacao': classificacao,
            'ticker': ticker_opcao,
            'strike': strike,
            'resumo': df_resumo,
            'melhor_pregoes': resumo_dados[idx_melhor]['Pregões Vol.'],
            'melhor_diferenca': resumo_dados[idx_melhor]['Diferença Média']
        }
    
    return None

def gerar_comparacao_geral(resultados):
    """
    Gera uma comparação geral entre as 3 opções.
    """
    print("\n" + "="*80)
    print("COMPARAÇÃO GERAL - ITM vs ATM vs OTM")
    print("="*80)
    
    # Organiza por classificação
    resultados_ordenados = sorted(resultados, key=lambda x: ['ATM', 'ITM', 'OTM'].index(x['classificacao']))
    
    print("\nMelhores períodos de volatilidade por opção:\n")
    
    comparacao_dados = []
    for r in resultados_ordenados:
        comparacao_dados.append({
            'Opção': r['ticker'],
            'Classificação': r['classificacao'],
            'Strike': f"R$ {r['strike']:.2f}",
            'Melhor Período': f"{r['melhor_pregoes']} pregões",
            'Diferença Média': r['melhor_diferenca']
        })
    
    df_comparacao = pd.DataFrame(comparacao_dados)
    print(df_comparacao.to_string(index=False))
    
    print("\n" + "="*80)
    
    # Salva resumo consolidado
    output_file = 'dados-comparacao-preco/resumo_ITM_ATM_OTM.csv'
    os.makedirs('dados-comparacao-preco', exist_ok=True)
    df_comparacao.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nResumo consolidado salvo em: {output_file}")
    
    return df_comparacao

def main():
    """
    Função principal.
    """
    print("\n" + "#"*80)
    print("# ANÁLISE COMPARATIVA: OPÇÕES ITM, ATM E OTM")
    print("# Períodos de Volatilidade: 30, 60, 120 e 252 pregões")
    print("#"*80)
    
    # Conecta ao banco de dados
    caminho_banco = 'banco/mercado_opcoes.db'
    conn = sqlite3.connect(caminho_banco)
    
    try:
        resultados = []
        
        # Analisa cada opção
        for opcao_config in OPCOES_ANALISAR:
            resultado = analisar_opcao(conn, opcao_config)
            if resultado:
                resultados.append(resultado)
                
                # Salva resumo individual
                output_file = f"dados-comparacao-preco/resumo_{opcao_config['ticker']}.csv"
                resultado['resumo'].to_csv(output_file, index=False, encoding='utf-8')
                print(f"  → Resumo salvo em: {output_file}")
        
        # Gera comparação geral
        if resultados:
            gerar_comparacao_geral(resultados)
        
        print("\n" + "#"*80)
        print("# ANÁLISE CONCLUÍDA!")
        print("#"*80 + "\n")
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()

