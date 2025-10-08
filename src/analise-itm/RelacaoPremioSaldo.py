#!/usr/bin/env python3
"""
Análise da Relação entre Prêmio da Opção e Resultado Final
Hipótese: opções ITM mais caras (prêmio alto) tendem a gerar resultados mais estáveis,
mas talvez com menor ganho percentual.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def configurar_estilo():
    """Configura o estilo dos gráficos para melhor visualização."""
    try:
        plt.style.use('seaborn-v0_8')
    except OSError:
        plt.style.use('seaborn')
    sns.set_palette("husl")
    
    # Configurações de fonte
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9

def carregar_dados():
    """Carrega os dados de todas as simulações."""
    dados = {}
    
    # Arquivos de simulação
    arquivos = {
        'Delta': 'dados/SimulacaoPeloDelta.xlsx',
        'Dia': 'dados/SimulacaoPeloDia.xlsx', 
        'Lote': 'dados/SimulacaoPeloLote.xlsx'
    }
    
    for estrategia, arquivo in arquivos.items():
        try:
            df = pd.read_excel(arquivo, sheet_name='Todos')
            dados[estrategia] = df
            print(f"Dados {estrategia} carregados: {df.shape}")
        except Exception as e:
            print(f"Erro ao carregar {arquivo}: {str(e)}")
    
    return dados

def preparar_dados(dados):
    """Prepara os dados para análise, calculando o prêmio inicial."""
    dados_preparados = {}
    
    for estrategia, df in dados.items():
        # Converter coluna 'Saldo Final' para numérico
        df['Saldo Final'] = df['Saldo Final'].str.replace('R$ ', '').str.replace(',', '.').astype(float)
        
        # Converter coluna 'Preço' para numérico (prêmio da opção)
        df['Preço'] = df['Preço'].str.replace('R$ ', '').str.replace(',', '.').astype(float)
        
        # Filtrar apenas simulações que começam com ITM
        df_itm = df[df['Simulação'].str.startswith('ITM', na=False)].copy()
        
        if not df_itm.empty:
            # Calcular prêmio inicial (preço da opção)
            df_itm['Premio_Inicial'] = df_itm['Preço']
            
            # Remover valores nulos
            df_clean = df_itm.dropna(subset=['Saldo Final', 'Premio_Inicial'])
            
            if len(df_clean) > 0:
                # Adicionar estratégia
                df_clean['Estrategia'] = estrategia
                
                dados_preparados[estrategia] = df_clean
                print(f"ITM {estrategia}: {len(df_clean)} observações")
                print(f"  Prêmio médio: R$ {df_clean['Premio_Inicial'].mean():.2f}")
                print(f"  Saldo médio: R$ {df_clean['Saldo Final'].mean():.2f}")
        else:
            print(f"Nenhuma simulação ITM encontrada para {estrategia}")
    
    return dados_preparados

def gerar_scatter_plot_premio_saldo(dados_preparados, output_dir):
    """Gera scatter plot prêmio × saldo final."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Relação entre Prêmio da Opção e Resultado Final\n(Simulações ITM)', 
                 fontsize=16, fontweight='bold')
    
    cores = ['blue', 'red', 'green']
    
    # Subplot 1: Scatter plot individual por estratégia
    for i, (estrategia, df) in enumerate(dados_preparados.items()):
        if i < 3:  # Máximo 3 estratégias
            ax = axes[0, i] if i < 2 else axes[1, 0]
            
            # Scatter plot
            ax.scatter(df['Premio_Inicial'], df['Saldo Final'], 
                      alpha=0.6, color=cores[i], s=30)
            
            # Linha de tendência
            z = np.polyfit(df['Premio_Inicial'], df['Saldo Final'], 1)
            p = np.poly1d(z)
            ax.plot(df['Premio_Inicial'], p(df['Premio_Inicial']), 
                   color='black', linestyle='--', alpha=0.8)
            
            # Correlação
            corr = df['Premio_Inicial'].corr(df['Saldo Final'])
            ax.set_title(f'{estrategia}\nCorrelação: {corr:.3f}')
            ax.set_xlabel('Prêmio Inicial (R$)')
            ax.set_ylabel('Saldo Final (R$)')
            ax.grid(True, alpha=0.3)
    
    # Subplot 4: Scatter plot combinado
    ax_combined = axes[1, 1]
    for i, (estrategia, df) in enumerate(dados_preparados.items()):
        ax_combined.scatter(df['Premio_Inicial'], df['Saldo Final'], 
                           alpha=0.6, color=cores[i], label=estrategia, s=30)
    
    ax_combined.set_title('Todas as Estratégias')
    ax_combined.set_xlabel('Prêmio Inicial (R$)')
    ax_combined.set_ylabel('Saldo Final (R$)')
    ax_combined.legend()
    ax_combined.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'scatter_premio_saldo_itm.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Scatter plot salvo em: {output_path}")
    
    plt.show()

def gerar_scatter_saldo_freq_ajuste(dados_preparados, output_dir):
    """Gera scatter plot saldo final × frequência de ajuste para estratégia Dia."""
    if 'Dia' not in dados_preparados:
        print("Estratégia 'Dia' não encontrada nos dados!")
        return
    
    df_dia = dados_preparados['Dia']
    
    # Converter coluna 'Freq.Ajuste' para numérico
    df_dia['Freq_Ajuste'] = pd.to_numeric(df_dia['Freq.Ajuste'], errors='coerce')
    
    # Remover valores nulos
    df_dia_clean = df_dia.dropna(subset=['Freq_Ajuste', 'Saldo Final'])
    
    plt.figure(figsize=(12, 8))
    
    # Scatter plot
    plt.scatter(df_dia_clean['Freq_Ajuste'], df_dia_clean['Saldo Final'], 
               alpha=0.6, color='red', s=30)
    
    # Linha de tendência
    z = np.polyfit(df_dia_clean['Freq_Ajuste'], df_dia_clean['Saldo Final'], 1)
    p = np.poly1d(z)
    plt.plot(df_dia_clean['Freq_Ajuste'], p(df_dia_clean['Freq_Ajuste']), 
             color='black', linestyle='--', alpha=0.8, linewidth=2)
    
    # Correlação
    corr = df_dia_clean['Freq_Ajuste'].corr(df_dia_clean['Saldo Final'])
    
    plt.title(f'Relação entre Frequência de Ajuste e Saldo Final\nDelta Hedge - Ajuste pelo Dia (ITM)\nCorrelação: {corr:.3f}', 
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Frequência de Ajuste (dias)', fontsize=12)
    plt.ylabel('Saldo Final (R$)', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'scatter_saldo_freq_ajuste_dia_itm.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Scatter plot saldo × frequência de ajuste salvo em: {output_path}")
    
    plt.show()

def gerar_estatisticas_descritivas(dados_preparados, output_dir):
    """Gera estatísticas descritivas detalhadas."""
    stats_file = output_dir / 'estatisticas_premio_saldo_itm.txt'
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("ESTATÍSTICAS DESCRITIVAS - RELAÇÃO PRÊMIO × SALDO FINAL (ITM)\n")
        f.write("=" * 70 + "\n\n")
        
        # Combinar todos os dados
        df_combined = pd.concat(dados_preparados.values(), ignore_index=True)
        
        # Estatísticas gerais
        f.write("ESTATÍSTICAS GERAIS (TODAS AS ESTRATÉGIAS):\n")
        f.write("-" * 50 + "\n")
        f.write(f"Total de observações ITM: {len(df_combined)}\n")
        f.write(f"Prêmio médio: R$ {df_combined['Premio_Inicial'].mean():.2f}\n")
        f.write(f"Prêmio desvio padrão: R$ {df_combined['Premio_Inicial'].std():.2f}\n")
        f.write(f"Prêmio mínimo: R$ {df_combined['Premio_Inicial'].min():.2f}\n")
        f.write(f"Prêmio máximo: R$ {df_combined['Premio_Inicial'].max():.2f}\n\n")
        
        f.write(f"Saldo Final médio: R$ {df_combined['Saldo Final'].mean():.2f}\n")
        f.write(f"Saldo Final desvio padrão: R$ {df_combined['Saldo Final'].std():.2f}\n")
        f.write(f"Saldo Final mínimo: R$ {df_combined['Saldo Final'].min():.2f}\n")
        f.write(f"Saldo Final máximo: R$ {df_combined['Saldo Final'].max():.2f}\n\n")
        
        # Correlação geral
        corr_geral = df_combined['Premio_Inicial'].corr(df_combined['Saldo Final'])
        f.write(f"Correlação geral (Prêmio × Saldo): {corr_geral:.4f}\n\n")
        
        # Por estratégia
        for estrategia, df in dados_preparados.items():
            f.write(f"ESTRATÉGIA: {estrategia}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Observações: {len(df)}\n")
            f.write(f"Prêmio médio: R$ {df['Premio_Inicial'].mean():.2f}\n")
            f.write(f"Saldo médio: R$ {df['Saldo Final'].mean():.2f}\n")
            f.write(f"Correlação: {df['Premio_Inicial'].corr(df['Saldo Final']):.4f}\n")
            f.write(f"R²: {df['Premio_Inicial'].corr(df['Saldo Final'])**2:.4f}\n\n")
        
    
    print(f"Estatísticas descritivas salvas em: {stats_file}")

def main():
    """Função principal."""
    # Configurar caminhos
    output_dir = Path('graficos/analise-itm')
    
    # Criar diretório de saída se não existir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("ANÁLISE DA RELAÇÃO ENTRE PRÊMIO DA OPÇÃO E RESULTADO FINAL (ITM)")
    print("=" * 80)
    
    # Configurar estilo
    configurar_estilo()
    
    # Carregar dados
    print("\nCarregando dados...")
    dados = carregar_dados()
    
    if not dados:
        print("❌ Nenhum dado carregado!")
        return
    
    # Preparar dados
    print("\nPreparando dados...")
    dados_preparados = preparar_dados(dados)
    
    if not dados_preparados:
        print("❌ Nenhum dado ITM encontrado!")
        return
    
    # Gerar análises
    print("\nGerando análises...")
    
    # Scatter plot prêmio × saldo
    gerar_scatter_plot_premio_saldo(dados_preparados, output_dir)
    
    # Scatter plot saldo × frequência de ajuste (estratégia Dia)
    gerar_scatter_saldo_freq_ajuste(dados_preparados, output_dir)
    
    # Estatísticas descritivas
    gerar_estatisticas_descritivas(dados_preparados, output_dir)
    
    print("\n" + "=" * 80)
    print("ANÁLISE CONCLUÍDA!")
    print("=" * 80)
    print(f"Gráficos salvos em: {output_dir}")
    print("Arquivos gerados:")
    print("- scatter_premio_saldo_itm.png")
    print("- scatter_saldo_freq_ajuste_dia_itm.png")
    print("- estatisticas_premio_saldo_itm.txt")

if __name__ == "__main__":
    main()
