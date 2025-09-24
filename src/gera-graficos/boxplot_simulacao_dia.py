import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def configurar_estilo():
    """Configura o estilo dos gráficos para melhor visualização."""
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Configurações de fonte
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9

def carregar_dados(arquivo_excel):
    """Carrega os dados da aba 'Todos' do arquivo Excel."""
    try:
        df = pd.read_excel(arquivo_excel, sheet_name='Todos')
        print(f"Dados carregados com sucesso!")
        print(f"Shape dos dados: {df.shape}")
        print(f"Colunas disponíveis: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"Erro ao carregar dados: {str(e)}")
        return None

def preparar_dados(df):
    """Prepara os dados para análise, convertendo colunas numéricas."""
    # Converter coluna 'Saldo Final' para numérico
    df['Saldo Final'] = df['Saldo Final'].str.replace('R$ ', '').str.replace(',', '.').astype(float)
    
    # Converter coluna 'Freq.Ajuste' para numérico
    df['Freq.Ajuste'] = pd.to_numeric(df['Freq.Ajuste'], errors='coerce')
    
    # Converter coluna '# Pregões Vol.' para numérico
    df['# Pregões Vol.'] = pd.to_numeric(df['# Pregões Vol.'], errors='coerce')
    
    # Remover linhas com valores nulos
    df_clean = df.dropna(subset=['Saldo Final', 'Freq.Ajuste', '# Pregões Vol.', 'Simulação'])
    
    print(f"Dados após limpeza: {df_clean.shape}")
    print(f"Valores únicos em 'Simulação': {df_clean['Simulação'].unique()}")
    print(f"Valores únicos em 'Freq.Ajuste': {sorted(df_clean['Freq.Ajuste'].unique())}")
    print(f"Valores únicos em '# Pregões Vol.': {sorted(df_clean['# Pregões Vol.'].unique())}")
    
    return df_clean

def gerar_boxplot_simulacao(df, output_dir):
    """Gera boxplot por categoria 'Simulação'."""
    plt.figure(figsize=(12, 8))
    
    # Criar boxplot sem preenchimento preto
    sns.boxplot(data=df, x='Simulação', y='Saldo Final', 
                palette='Set2', linewidth=1.5)
    
    plt.title('Distribuição do Saldo Final por Categoria de Simulação\n(Delta Hedge - Ajuste por Dia)', 
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Categoria de Simulação', fontsize=12)
    plt.ylabel('Saldo Final (R$)', fontsize=12)
    
    # Rotacionar labels do eixo x se necessário
    plt.xticks(rotation=45)
    
    # Adicionar grid
    plt.grid(True, alpha=0.3)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'boxplot_simulacao_dia.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Boxplot por Simulação salvo em: {output_path}")
    
    plt.show()

def gerar_boxplot_freq_ajuste(df, output_dir):
    """Gera boxplot por 'Freq.Ajuste'."""
    plt.figure(figsize=(14, 8))
    
    # Criar boxplot sem preenchimento preto
    sns.boxplot(data=df, x='Freq.Ajuste', y='Saldo Final', 
                palette='Set3', linewidth=1.5)
    
    plt.title('Distribuição do Saldo Final por Frequência de Ajuste\n(Delta Hedge - Ajuste por Dia)', 
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Frequência de Ajuste (dias)', fontsize=12)
    plt.ylabel('Saldo Final (R$)', fontsize=12)
    
    # Adicionar grid
    plt.grid(True, alpha=0.3)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'boxplot_freq_ajuste.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Boxplot por Frequência de Ajuste salvo em: {output_path}")
    
    plt.show()

def gerar_boxplot_pregões_vol(df, output_dir):
    """Gera boxplot por '# Pregões Vol.'."""
    plt.figure(figsize=(14, 8))
    
    # Criar boxplot sem preenchimento preto
    sns.boxplot(data=df, x='# Pregões Vol.', y='Saldo Final', 
                palette='Set1', linewidth=1.5)
    
    plt.title('Distribuição do Saldo Final por Período de Volatilidade\n(Delta Hedge - Ajuste por Dia)', 
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Período de Volatilidade (pregões)', fontsize=12)
    plt.ylabel('Saldo Final (R$)', fontsize=12)
    
    # Adicionar grid
    plt.grid(True, alpha=0.3)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'boxplot_pregões_vol_dia.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Boxplot por Pregões Vol. salvo em: {output_path}")
    
    plt.show()

def gerar_boxplot_combinado(df, output_dir):
    """Gera boxplot combinando Frequência de Ajuste e Pregões Vol."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Análise Combinada: Frequência de Ajuste vs Período de Volatilidade\n(Delta Hedge - Ajuste por Dia)', 
                 fontsize=16, fontweight='bold')
    
    # Subplot 1: Boxplot por Frequência de Ajuste
    sns.boxplot(data=df, x='Freq.Ajuste', y='Saldo Final', 
                palette='Set2', linewidth=1.5, ax=axes[0,0])
    axes[0,0].set_title('Saldo Final por Frequência de Ajuste')
    axes[0,0].set_xlabel('Frequência de Ajuste (dias)')
    axes[0,0].set_ylabel('Saldo Final (R$)')
    axes[0,0].grid(True, alpha=0.3)
    
    # Subplot 2: Boxplot por Pregões Vol
    sns.boxplot(data=df, x='# Pregões Vol.', y='Saldo Final', 
                palette='Set3', linewidth=1.5, ax=axes[0,1])
    axes[0,1].set_title('Saldo Final por Período de Volatilidade')
    axes[0,1].set_xlabel('Período de Volatilidade (pregões)')
    axes[0,1].set_ylabel('Saldo Final (R$)')
    axes[0,1].grid(True, alpha=0.3)
    
    # Subplot 3: Boxplot por Simulação
    sns.boxplot(data=df, x='Simulação', y='Saldo Final', 
                palette='Set1', linewidth=1.5, ax=axes[1,0])
    axes[1,0].set_title('Saldo Final por Categoria de Simulação')
    axes[1,0].set_xlabel('Categoria de Simulação')
    axes[1,0].set_ylabel('Saldo Final (R$)')
    axes[1,0].tick_params(axis='x', rotation=45)
    axes[1,0].grid(True, alpha=0.3)
    
    # Subplot 4: Violin plot combinado
    sns.violinplot(data=df, x='Freq.Ajuste', y='Saldo Final', 
                   hue='# Pregões Vol.', palette='Set2', ax=axes[1,1])
    axes[1,1].set_title('Distribuição por Frequência e Volatilidade')
    axes[1,1].set_xlabel('Frequência de Ajuste (dias)')
    axes[1,1].set_ylabel('Saldo Final (R$)')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'boxplot_combinado_dia.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Boxplot combinado salvo em: {output_path}")
    
    plt.show()

def gerar_boxplot_estados_delta_detalhado(df, output_dir):
    """Gera boxplot com análise detalhada dos estados do delta."""
    # Criar colunas para estado inicial e final do delta
    df['Estado_Inicial_Delta'] = df['Simulação'].str.split(' → ').str[0]
    df['Estado_Final_Delta'] = df['Simulação'].str.split(' → ').str[1]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Análise Detalhada dos Estados do Delta\n(Delta Hedge - Ajuste por Dia)', 
                 fontsize=16, fontweight='bold')
    
    # Subplot 1: Boxplot por estado completo do delta
    sns.boxplot(data=df, x='Simulação', y='Saldo Final', 
                palette='Set2', linewidth=1.5, ax=axes[0,0])
    axes[0,0].set_title('Saldo Final por Estado Completo do Delta')
    axes[0,0].set_xlabel('Estado do Delta (Inicial → Final)')
    axes[0,0].set_ylabel('Saldo Final (R$)')
    axes[0,0].tick_params(axis='x', rotation=45)
    axes[0,0].grid(True, alpha=0.3)
    
    # Subplot 2: Boxplot por estado inicial do delta
    sns.boxplot(data=df, x='Estado_Inicial_Delta', y='Saldo Final', 
                palette='Set3', linewidth=1.5, ax=axes[0,1])
    axes[0,1].set_title('Saldo Final por Estado Inicial do Delta')
    axes[0,1].set_xlabel('Estado Inicial do Delta')
    axes[0,1].set_ylabel('Saldo Final (R$)')
    axes[0,1].grid(True, alpha=0.3)
    
    # Subplot 3: Boxplot por estado final do delta
    sns.boxplot(data=df, x='Estado_Final_Delta', y='Saldo Final', 
                palette='Set1', linewidth=1.5, ax=axes[1,0])
    axes[1,0].set_title('Saldo Final por Estado Final do Delta')
    axes[1,0].set_xlabel('Estado Final do Delta')
    axes[1,0].set_ylabel('Saldo Final (R$)')
    axes[1,0].grid(True, alpha=0.3)
    
    # Subplot 4: Violin plot para estado inicial ITM (Frequência Ajuste e Volatilidade)
    df_itm = df[df['Estado_Inicial_Delta'] == 'ITM'].copy()
    if not df_itm.empty:
        sns.violinplot(data=df_itm, x='Freq.Ajuste', y='Saldo Final', 
                       hue='# Pregões Vol.', palette='Set2', ax=axes[1,1])
        axes[1,1].set_title('Distribuição Inicial ITM: Frequência Ajuste e Volatilidade')
        axes[1,1].set_xlabel('Frequência de Ajuste (dias)')
        axes[1,1].set_ylabel('Saldo Final (R$)')
        axes[1,1].grid(True, alpha=0.3)
    else:
        axes[1,1].text(0.5, 0.5, 'Sem dados ITM', ha='center', va='center', transform=axes[1,1].transAxes)
        axes[1,1].set_title('Distribuição Inicial ITM: Frequência Ajuste e Volatilidade')
        axes[1,1].set_xlabel('Frequência de Ajuste (dias)')
        axes[1,1].set_ylabel('Saldo Final (R$)')
    
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'boxplot_estados_delta_detalhado_dia.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Boxplot de estados do delta detalhado salvo em: {output_path}")
    
    plt.show()

def gerar_heatmap_correlacao(df, output_dir):
    """Gera heatmap de correlação entre variáveis numéricas."""
    plt.figure(figsize=(10, 8))
    
    # Selecionar apenas colunas numéricas
    numeric_cols = ['Saldo Final', 'Freq.Ajuste', '# Pregões Vol.', '# Ajustes']
    df_numeric = df[numeric_cols]
    
    # Calcular correlação
    correlation_matrix = df_numeric.corr()
    
    # Criar heatmap
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                square=True, fmt='.3f', cbar_kws={'shrink': 0.8})
    
    plt.title('Matriz de Correlação - Variáveis Numéricas\n(Delta Hedge - Ajuste por Dia)', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'heatmap_correlacao_dia.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Heatmap de correlação salvo em: {output_path}")
    
    plt.show()

def gerar_estatisticas_descritivas(df, output_dir):
    """Gera estatísticas descritivas e salva em arquivo."""
    stats_file = output_dir / 'estatisticas_descritivas_dia.txt'
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("ESTATÍSTICAS DESCRITIVAS - DELTA HEDGE AJUSTE POR DIA\n")
        f.write("=" * 60 + "\n\n")
        
        # Estatísticas gerais
        f.write("ESTATÍSTICAS GERAIS:\n")
        f.write(f"Total de observações: {len(df)}\n")
        f.write(f"Saldo Final - Média: R$ {df['Saldo Final'].mean():.2f}\n")
        f.write(f"Saldo Final - Mediana: R$ {df['Saldo Final'].median():.2f}\n")
        f.write(f"Saldo Final - Desvio Padrão: R$ {df['Saldo Final'].std():.2f}\n")
        f.write(f"Saldo Final - Mínimo: R$ {df['Saldo Final'].min():.2f}\n")
        f.write(f"Saldo Final - Máximo: R$ {df['Saldo Final'].max():.2f}\n\n")
        
        # Por categoria de simulação
        f.write("POR CATEGORIA DE SIMULAÇÃO:\n")
        f.write("-" * 40 + "\n")
        for categoria in df['Simulação'].unique():
            subset = df[df['Simulação'] == categoria]
            f.write(f"\n{categoria}:\n")
            f.write(f"  Observações: {len(subset)}\n")
            f.write(f"  Média: R$ {subset['Saldo Final'].mean():.2f}\n")
            f.write(f"  Mediana: R$ {subset['Saldo Final'].median():.2f}\n")
            f.write(f"  Desvio Padrão: R$ {subset['Saldo Final'].std():.2f}\n")
        
        # Por frequência de ajuste
        f.write("\n\nPOR FREQUÊNCIA DE AJUSTE:\n")
        f.write("-" * 40 + "\n")
        for freq in sorted(df['Freq.Ajuste'].unique()):
            subset = df[df['Freq.Ajuste'] == freq]
            f.write(f"\nFrequência {freq} dias:\n")
            f.write(f"  Observações: {len(subset)}\n")
            f.write(f"  Média: R$ {subset['Saldo Final'].mean():.2f}\n")
            f.write(f"  Mediana: R$ {subset['Saldo Final'].median():.2f}\n")
            f.write(f"  Desvio Padrão: R$ {subset['Saldo Final'].std():.2f}\n")
        
        # Por período de volatilidade
        f.write("\n\nPOR PERÍODO DE VOLATILIDADE:\n")
        f.write("-" * 40 + "\n")
        for periodo in sorted(df['# Pregões Vol.'].unique()):
            subset = df[df['# Pregões Vol.'] == periodo]
            f.write(f"\n{periodo} pregões:\n")
            f.write(f"  Observações: {len(subset)}\n")
            f.write(f"  Média: R$ {subset['Saldo Final'].mean():.2f}\n")
            f.write(f"  Mediana: R$ {subset['Saldo Final'].median():.2f}\n")
            f.write(f"  Desvio Padrão: R$ {subset['Saldo Final'].std():.2f}\n")
    
    print(f"Estatísticas descritivas salvas em: {stats_file}")

def main():
    """Função principal."""
    # Configurar caminhos
    arquivo_excel = Path('dados/SimulacaoPeloDia.xlsx')
    output_dir = Path('graficos')
    
    # Criar diretório de saída se não existir
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("GERADOR DE BOXPLOTS - DELTA HEDGE AJUSTE POR DIA")
    print("=" * 60)
    
    # Configurar estilo
    configurar_estilo()
    
    # Carregar dados
    df = carregar_dados(arquivo_excel)
    if df is None:
        return
    
    # Preparar dados
    df_clean = preparar_dados(df)
    
    # Gerar gráficos
    print("\nGerando boxplots...")
    
    # Boxplot de estados do delta detalhado
    gerar_boxplot_estados_delta_detalhado(df_clean, output_dir)
    
    # Heatmap de correlação
    gerar_heatmap_correlacao(df_clean, output_dir)
    
    # Estatísticas descritivas
    gerar_estatisticas_descritivas(df_clean, output_dir)
    
    print("\n" + "=" * 60)
    print("ANÁLISE CONCLUÍDA!")
    print("=" * 60)
    print(f"Gráficos salvos em: {output_dir}")
    print("Arquivos gerados:")
    print("- boxplot_estados_delta_detalhado_dia.png")
    print("- heatmap_correlacao_dia.png")
    print("- estatisticas_descritivas_dia.txt")

if __name__ == "__main__":
    main()
