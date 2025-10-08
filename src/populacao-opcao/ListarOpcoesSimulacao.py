#!/usr/bin/env python3
"""
Lista todas as opções utilizadas nas simulações de delta hedge.
Para cada opção informa: ticker, strike, vencimento, data início, preço opção, preço abertura PETR.
"""

import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def obter_dados_simulacoes():
    """Obtém dados das simulações dos arquivos Excel."""
    dados_simulacoes = {}
    
    arquivos = {
        'Delta': 'dados/SimulacaoPeloDelta.xlsx',
        'Dia': 'dados/SimulacaoPeloDia.xlsx',
        'Lote': 'dados/SimulacaoPeloLote.xlsx'
    }
    
    for estrategia, arquivo in arquivos.items():
        try:
            df = pd.read_excel(arquivo, sheet_name='Todos')
            dados_simulacoes[estrategia] = df
            print(f"Dados {estrategia} carregados: {df.shape}")
        except Exception as e:
            print(f"Erro ao carregar {arquivo}: {str(e)}")
    
    return dados_simulacoes

def processar_dados_simulacoes(dados_simulacoes):
    """Processa dados das simulações para extrair informações das opções."""
    opcoes_detalhadas = []
    
    for estrategia, df_sim in dados_simulacoes.items():
        if not df_sim.empty:
            print(f"Processando {len(df_sim)} simulações da estratégia {estrategia}...")
            
            for idx, row in df_sim.iterrows():
                # Extrair informações da simulação
                ticker = row['Opção'] if pd.notna(row['Opção']) else None
                strike = float(str(row['Strike']).replace('R$ ', '').replace(',', '.')) if pd.notna(row['Strike']) else None
                vencimento = row['Vencimento'] if pd.notna(row['Vencimento']) else None
                
                if ticker and strike:
                    # Converter colunas de preço para numérico
                    try:
                        preco_inicial = float(str(row['PETR-Início']).replace('R$ ', '').replace(',', '.'))
                        preco_opcao = float(str(row['Preço']).replace('R$ ', '').replace(',', '.'))
                    except Exception as e:
                        print(f"Erro ao processar linha {idx}: {str(e)}")
                        print(f"Ticker: {ticker}, Strike: {strike}")
                        continue
                    
                    # Criar entrada da opção
                    opcao_info = {
                        'Opcao': ticker,
                        'Strike': strike,
                        'Data_Vencimento': vencimento,
                        'Data_Inicio_Simulacao': row['Início'],
                        'Preco_Opcao': preco_opcao,
                        'Preco_Abertura_PETR': preco_inicial
                    }
                    
                    opcoes_detalhadas.append(opcao_info)
    
    if opcoes_detalhadas:
        df_opcoes = pd.DataFrame(opcoes_detalhadas)
        
        # Remover duplicatas baseado nas colunas principais
        df_opcoes = df_opcoes.drop_duplicates(subset=['Opcao', 'Strike', 'Data_Vencimento', 'Data_Inicio_Simulacao'])
        
        # Adicionar formatação
        df_opcoes['Strike_Formatado'] = df_opcoes['Strike'].apply(lambda x: f"R$ {x:.2f}" if pd.notna(x) else "N/A")
        df_opcoes['Preco_Opcao_Formatado'] = df_opcoes['Preco_Opcao'].apply(lambda x: f"R$ {x:.2f}" if pd.notna(x) else "N/A")
        df_opcoes['Preco_Abertura_PETR_Formatado'] = df_opcoes['Preco_Abertura_PETR'].apply(lambda x: f"R$ {x:.2f}" if pd.notna(x) else "N/A")
        
        return df_opcoes
    else:
        return None

def gerar_relatorio_opcoes(df_opcoes, output_dir):
    """Gera relatório detalhado das opções."""
    if df_opcoes is None or df_opcoes.empty:
        print("Nenhum dado para gerar relatório!")
        return
    
    # Criar diretório de saída
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Arquivo de relatório
    relatorio_file = output_dir / 'relatorio_opcoes_simulacao.txt'
    
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO SIMPLIFICADO DE OPÇÕES UTILIZADAS NAS SIMULAÇÕES\n")
        f.write("=" * 70 + "\n\n")
        
        # Estatísticas gerais
        f.write("ESTATÍSTICAS GERAIS:\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total de simulações: {len(df_opcoes)}\n")
        f.write(f"Opções únicas: {df_opcoes['Opcao'].nunique()}\n\n")
        
        # Detalhes das opções
        f.write("DETALHES DAS OPÇÕES:\n")
        f.write("-" * 20 + "\n\n")
        
        for idx, row in df_opcoes.iterrows():
            f.write(f"SIMULAÇÃO {idx + 1}:\n")
            f.write(f"  Opção: {row['Opcao']}\n")
            f.write(f"  Strike: {row['Strike_Formatado']}\n")
            f.write(f"  Data Vencimento: {row['Data_Vencimento']}\n")
            f.write(f"  Data Início Simulação: {row['Data_Inicio_Simulacao']}\n")
            f.write(f"  Preço Opção: {row['Preco_Opcao_Formatado']}\n")
            f.write(f"  Preço Abertura PETR: {row['Preco_Abertura_PETR_Formatado']}\n")
            f.write("\n")
    
    print(f"Relatório salvo em: {relatorio_file}")
    
    # Arquivo CSV para análise
    csv_file = output_dir / 'opcoes_simulacao.csv'
    df_opcoes.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"Arquivo CSV salvo em: {csv_file}")

def main():
    """Função principal."""
    print("=" * 80)
    print("LISTAGEM DE OPÇÕES UTILIZADAS NAS SIMULAÇÕES")
    print("=" * 80)
    
    # Configurar diretório de saída
    output_dir = Path('graficos/populacao-opcao')
    
    # Obter dados das simulações
    print("Obtendo dados das simulações...")
    dados_simulacoes = obter_dados_simulacoes()
    
    if not dados_simulacoes:
        print("Nenhum dado de simulação encontrado!")
        return
    
    # Processar dados
    print("Processando dados das simulações...")
    df_opcoes_processado = processar_dados_simulacoes(dados_simulacoes)
    
    if df_opcoes_processado is None:
        print("Nenhum dado processado!")
        return
    
    # Gerar relatório
    print("Gerando relatório...")
    gerar_relatorio_opcoes(df_opcoes_processado, output_dir)
    
    print("\n" + "=" * 80)
    print("PROCESSAMENTO CONCLUÍDO!")
    print("=" * 80)
    print(f"Relatórios salvos em: {output_dir}")

if __name__ == "__main__":
    main()
