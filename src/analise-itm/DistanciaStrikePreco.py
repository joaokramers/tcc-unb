#!/usr/bin/env python3
"""
Análise da Distância entre Strike e Preço do Ativo
Hipótese: quanto mais ITM no início (strike bem abaixo do preço do ativo), 
maior a probabilidade de ganhos consistentes, pois o delta inicial já é próximo de 1.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score
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
    """Prepara os dados para análise, calculando a distância strike-preço."""
    dados_preparados = {}
    
    for estrategia, df in dados.items():
        # Converter colunas para numérico
        df['Saldo Final'] = df['Saldo Final'].str.replace('R$ ', '').str.replace(',', '.').astype(float)
        df['Strike'] = df['Strike'].str.replace('R$ ', '').str.replace(',', '.').astype(float)
        df['PETR-Início'] = df['PETR-Início'].str.replace('R$ ', '').str.replace(',', '.').astype(float)
        df['Preço'] = df['Preço'].str.replace('R$ ', '').str.replace(',', '.').astype(float)
        
        # Filtrar apenas simulações que começam com ITM
        df_itm = df[df['Simulação'].str.startswith('ITM', na=False)].copy()
        
        if not df_itm.empty:
            # Calcular distância: (Preço do Ativo - Strike) / Strike
            df_itm['Distancia'] = (df_itm['PETR-Início'] - df_itm['Strike']) / df_itm['Strike']
            
            # Converter para percentual
            df_itm['Distancia_Pct'] = df_itm['Distancia'] * 100
            
            # Adicionar prêmio inicial
            df_itm['Premio_Inicial'] = df_itm['Preço']
            
            # Remover valores nulos
            df_clean = df_itm.dropna(subset=['Saldo Final', 'Distancia_Pct', 'Premio_Inicial'])
            
            if len(df_clean) > 0:
                # Adicionar estratégia
                df_clean['Estrategia'] = estrategia
                
                dados_preparados[estrategia] = df_clean
                print(f"ITM {estrategia}: {len(df_clean)} observações")
                print(f"  Distância média: {df_clean['Distancia_Pct'].mean():.2f}%")
                print(f"  Saldo médio: R$ {df_clean['Saldo Final'].mean():.2f}")
        else:
            print(f"Nenhuma simulação ITM encontrada para {estrategia}")
    
    return dados_preparados


def gerar_analise_faixas_distancia(dados_preparados, output_dir):
    """Gera análise por faixas de distância."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Análise por Faixas de Distância Strike-Preço\n(Simulações ITM)', 
                 fontsize=16, fontweight='bold')
    
    # Combinar todos os dados
    df_combined = pd.concat(dados_preparados.values(), ignore_index=True)
    
    # Criar faixas de distância
    faixas = [0, 2.5, 5, 7.5, 10]
    labels = ['0-2.5%', '2.5-5%', '5-7.5%', '7.5-10%']
    df_combined['Faixa_Distancia'] = pd.cut(df_combined['Distancia_Pct'], 
                                           bins=faixas, labels=labels, include_lowest=True)
    
    # Subplot 1: Boxplot por faixa de distância
    sns.boxplot(data=df_combined, x='Faixa_Distancia', y='Saldo Final', ax=axes[0, 0])
    axes[0, 0].set_title('Distribuição do Saldo Final por Faixa de Distância')
    axes[0, 0].set_xlabel('Faixa de Distância (%)')
    axes[0, 0].set_ylabel('Saldo Final (R$)')
    axes[0, 0].tick_params(axis='x', rotation=45)
    axes[0, 0].grid(True, alpha=0.3)
    
    # Subplot 2: Boxplot por faixa de distância (apenas estratégia Delta)
    df_delta = df_combined[df_combined['Estrategia'] == 'Delta']
    sns.boxplot(data=df_delta, x='Faixa_Distancia', y='Saldo Final', ax=axes[0, 1])
    axes[0, 1].set_title('Distribuição do Saldo Final por Faixa de Distância\n(Estratégia Delta)')
    axes[0, 1].set_xlabel('Faixa de Distância (%)')
    axes[0, 1].set_ylabel('Saldo Final (R$)')
    axes[0, 1].tick_params(axis='x', rotation=45)
    axes[0, 1].grid(True, alpha=0.3)
    
    # Subplot 3: Boxplot por faixa de distância (apenas estratégia Dia)
    df_dia = df_combined[df_combined['Estrategia'] == 'Dia']
    sns.boxplot(data=df_dia, x='Faixa_Distancia', y='Saldo Final', ax=axes[1, 0])
    axes[1, 0].set_title('Distribuição do Saldo Final por Faixa de Distância\n(Estratégia Dia)')
    axes[1, 0].set_xlabel('Faixa de Distância (%)')
    axes[1, 0].set_ylabel('Saldo Final (R$)')
    axes[1, 0].tick_params(axis='x', rotation=45)
    axes[1, 0].grid(True, alpha=0.3)
    
    # Subplot 4: Boxplot por faixa de distância (apenas estratégia Lote)
    df_lote = df_combined[df_combined['Estrategia'] == 'Lote']
    sns.boxplot(data=df_lote, x='Faixa_Distancia', y='Saldo Final', ax=axes[1, 1])
    axes[1, 1].set_title('Distribuição do Saldo Final por Faixa de Distância\n(Estratégia Lote)')
    axes[1, 1].set_xlabel('Faixa de Distância (%)')
    axes[1, 1].set_ylabel('Saldo Final (R$)')
    axes[1, 1].tick_params(axis='x', rotation=45)
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Salvar gráfico
    output_path = output_dir / 'analise_faixas_distancia_itm.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Análise por faixas salva em: {output_path}")
    
    plt.show()

def gerar_estatisticas_descritivas(dados_preparados, output_dir):
    """Gera estatísticas descritivas detalhadas."""
    stats_file = output_dir / 'estatisticas_distancia_strike_itm.txt'
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("ESTATÍSTICAS DESCRITIVAS - DISTÂNCIA STRIKE-PREÇO (ITM)\n")
        f.write("=" * 70 + "\n\n")
        
        # Combinar todos os dados
        df_combined = pd.concat(dados_preparados.values(), ignore_index=True)
        
        # Estatísticas gerais
        f.write("ESTATÍSTICAS GERAIS (TODAS AS ESTRATÉGIAS):\n")
        f.write("-" * 50 + "\n")
        f.write(f"Total de observações ITM: {len(df_combined)}\n")
        f.write(f"Distância média: {df_combined['Distancia_Pct'].mean():.2f}%\n")
        f.write(f"Distância desvio padrão: {df_combined['Distancia_Pct'].std():.2f}%\n")
        f.write(f"Distância mínima: {df_combined['Distancia_Pct'].min():.2f}%\n")
        f.write(f"Distância máxima: {df_combined['Distancia_Pct'].max():.2f}%\n\n")
        
        f.write(f"Saldo Final médio: R$ {df_combined['Saldo Final'].mean():.2f}\n")
        f.write(f"Saldo Final desvio padrão: R$ {df_combined['Saldo Final'].std():.2f}\n")
        f.write(f"Saldo Final mínimo: R$ {df_combined['Saldo Final'].min():.2f}\n")
        f.write(f"Saldo Final máximo: R$ {df_combined['Saldo Final'].max():.2f}\n\n")
        
        # Correlação geral
        corr_geral = df_combined['Distancia_Pct'].corr(df_combined['Saldo Final'])
        f.write(f"Correlação geral (Distância × Saldo): {corr_geral:.4f}\n\n")
        
        # Por estratégia
        for estrategia, df in dados_preparados.items():
            f.write(f"ESTRATÉGIA: {estrategia}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Observações: {len(df)}\n")
            f.write(f"Distância média: {df['Distancia_Pct'].mean():.2f}%\n")
            f.write(f"Saldo médio: R$ {df['Saldo Final'].mean():.2f}\n")
            f.write(f"Correlação: {df['Distancia_Pct'].corr(df['Saldo Final']):.4f}\n")
            f.write(f"R²: {df['Distancia_Pct'].corr(df['Saldo Final'])**2:.4f}\n\n")
        
        # Análise por faixas de distância
        f.write("ANÁLISE POR FAIXAS DE DISTÂNCIA:\n")
        f.write("-" * 40 + "\n")
        
        faixas = [0, 2.5, 5, 7.5, 10]
        labels = ['0-2.5%', '2.5-5%', '5-7.5%', '7.5-10%']
        df_combined['Faixa_Distancia'] = pd.cut(df_combined['Distancia_Pct'], 
                                               bins=faixas, labels=labels, include_lowest=True)
        
        for faixa in df_combined['Faixa_Distancia'].cat.categories:
            subset = df_combined[df_combined['Faixa_Distancia'] == faixa]
            if not subset.empty:
                f.write(f"\n{faixa}:\n")
                f.write(f"  Observações: {len(subset)}\n")
                f.write(f"  Distância média: {subset['Distancia_Pct'].mean():.2f}%\n")
                f.write(f"  Saldo médio: R$ {subset['Saldo Final'].mean():.2f}\n")
                f.write(f"  Saldo desvio padrão: R$ {subset['Saldo Final'].std():.2f}\n")
                f.write(f"  Coeficiente de variação: {subset['Saldo Final'].std() / subset['Saldo Final'].mean():.4f}\n")
    
    print(f"Estatísticas descritivas salvas em: {stats_file}")

def gerar_analise_estatistica_avancada(dados_preparados, output_dir):
    """Gera análise estatística avançada com regressão múltipla e correlações parciais."""
    stats_file = output_dir / 'analise_estatistica_avancada_itm.txt'
    
    # Combinar todos os dados
    df_combined = pd.concat(dados_preparados.values(), ignore_index=True)
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("ANÁLISE ESTATÍSTICA AVANÇADA - DISTÂNCIA STRIKE-PREÇO (ITM)\n")
        f.write("=" * 70 + "\n\n")
        
        # 1. Regressão Linear Múltipla
        f.write("1. REGRESSÃO LINEAR MÚLTIPLA\n")
        f.write("-" * 40 + "\n")
        f.write("Modelo: SaldoFinal = α + β₁ · Prêmio + β₂ · Distância + ε\n\n")
        
        # Preparar dados para regressão
        X = df_combined[['Premio_Inicial', 'Distancia_Pct']].values
        y = df_combined['Saldo Final'].values
        
        # Regressão linear múltipla
        model = LinearRegression()
        model.fit(X, y)
        
        # Predições
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        f.write(f"Coeficientes:\n")
        f.write(f"  α (intercepto): {model.intercept_:.2f}\n")
        f.write(f"  β₁ (prêmio): {model.coef_[0]:.4f}\n")
        f.write(f"  β₂ (distância): {model.coef_[1]:.4f}\n")
        f.write(f"R²: {r2:.4f}\n")
        f.write(f"R² ajustado: {1 - (1 - r2) * (len(y) - 1) / (len(y) - X.shape[1] - 1):.4f}\n\n")
        
        # Interpretação dos coeficientes
        f.write("Interpretação:\n")
        f.write(f"  - Aumento de R$ 1 no prêmio inicial resulta em {model.coef_[0]:.2f} no saldo final\n")
        f.write(f"  - Aumento de 1% na distância resulta em {model.coef_[1]:.2f} no saldo final\n")
        f.write(f"  - {r2*100:.1f}% da variância do saldo final é explicada pelo modelo\n\n")
        
        # 2. Correlações Parciais
        f.write("2. CORRELAÇÕES PARCIAIS\n")
        f.write("-" * 30 + "\n")
        
        # Correlação parcial entre Saldo e Prêmio (controlando Distância)
        corr_saldo_premio = df_combined['Saldo Final'].corr(df_combined['Premio_Inicial'])
        corr_saldo_distancia = df_combined['Saldo Final'].corr(df_combined['Distancia_Pct'])
        corr_premio_distancia = df_combined['Premio_Inicial'].corr(df_combined['Distancia_Pct'])
        
        # Fórmula da correlação parcial
        corr_parcial_saldo_premio = (corr_saldo_premio - corr_saldo_distancia * corr_premio_distancia) / \
                                   np.sqrt((1 - corr_saldo_distancia**2) * (1 - corr_premio_distancia**2))
        
        corr_parcial_saldo_distancia = (corr_saldo_distancia - corr_saldo_premio * corr_premio_distancia) / \
                                      np.sqrt((1 - corr_saldo_premio**2) * (1 - corr_premio_distancia**2))
        
        f.write("Correlações simples:\n")
        f.write(f"  Saldo × Prêmio: {corr_saldo_premio:.4f}\n")
        f.write(f"  Saldo × Distância: {corr_saldo_distancia:.4f}\n")
        f.write(f"  Prêmio × Distância: {corr_premio_distancia:.4f}\n\n")
        
        f.write("Correlações parciais:\n")
        f.write(f"  Saldo × Prêmio (controlando Distância): {corr_parcial_saldo_premio:.4f}\n")
        f.write(f"  Saldo × Distância (controlando Prêmio): {corr_parcial_saldo_distancia:.4f}\n\n")
        
        # 3. Verificação de Não-linearidades
        f.write("3. VERIFICAÇÃO DE NÃO-LINEARIDADES\n")
        f.write("-" * 40 + "\n")
        
        # Regressão polinomial (termos quadráticos)
        poly_features = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly_features.fit_transform(X)
        
        model_poly = LinearRegression()
        model_poly.fit(X_poly, y)
        
        y_pred_poly = model_poly.predict(X_poly)
        r2_poly = r2_score(y, y_pred_poly)
        
        f.write("Modelo com termos quadráticos:\n")
        f.write(f"  SaldoFinal = α + β₁·Prêmio + β₂·Distância + β₃·Prêmio² + β₄·Distância² + β₅·Prêmio·Distância + ε\n\n")
        
        f.write("Coeficientes do modelo polinomial:\n")
        f.write(f"  α (intercepto): {model_poly.intercept_:.2f}\n")
        f.write(f"  β₁ (prêmio): {model_poly.coef_[0]:.4f}\n")
        f.write(f"  β₂ (distância): {model_poly.coef_[1]:.4f}\n")
        f.write(f"  β₃ (prêmio²): {model_poly.coef_[2]:.4f}\n")
        f.write(f"  β₄ (distância²): {model_poly.coef_[3]:.4f}\n")
        f.write(f"  β₅ (prêmio×distância): {model_poly.coef_[4]:.4f}\n")
        f.write(f"R²: {r2_poly:.4f}\n\n")
        
        # Comparação dos modelos
        f.write("Comparação dos modelos:\n")
        f.write(f"  Modelo linear: R² = {r2:.4f}\n")
        f.write(f"  Modelo polinomial: R² = {r2_poly:.4f}\n")
        f.write(f"  Melhoria: {r2_poly - r2:.4f} ({(r2_poly - r2)/r2*100:.1f}%)\n\n")
        
        if r2_poly > r2 + 0.01:  # Melhoria significativa
            f.write("  → Há evidência de não-linearidades significativas\n")
        else:
            f.write("  → Não há evidência forte de não-linearidades\n")
        
        # 4. Análise por Estratégia
        f.write("\n4. ANÁLISE POR ESTRATÉGIA\n")
        f.write("-" * 30 + "\n")
        
        for estrategia, df in dados_preparados.items():
            f.write(f"\nEstratégia: {estrategia}\n")
            f.write("-" * 20 + "\n")
            
            X_estr = df[['Premio_Inicial', 'Distancia_Pct']].values
            y_estr = df['Saldo Final'].values
            
            # Regressão linear
            model_estr = LinearRegression()
            model_estr.fit(X_estr, y_estr)
            y_pred_estr = model_estr.predict(X_estr)
            r2_estr = r2_score(y_estr, y_pred_estr)
            
            f.write(f"  Coeficientes:\n")
            f.write(f"    α: {model_estr.intercept_:.2f}\n")
            f.write(f"    β₁ (prêmio): {model_estr.coef_[0]:.4f}\n")
            f.write(f"    β₂ (distância): {model_estr.coef_[1]:.4f}\n")
            f.write(f"  R²: {r2_estr:.4f}\n")
            
            # Correlações
            corr_premio = df['Saldo Final'].corr(df['Premio_Inicial'])
            corr_distancia = df['Saldo Final'].corr(df['Distancia_Pct'])
            f.write(f"  Correlações:\n")
            f.write(f"    Saldo × Prêmio: {corr_premio:.4f}\n")
            f.write(f"    Saldo × Distância: {corr_distancia:.4f}\n")
    
    print(f"Análise estatística avançada salva em: {stats_file}")

def main():
    """Função principal."""
    # Configurar caminhos
    output_dir = Path('graficos/analise-itm-premio')
    
    # Criar diretório de saída se não existir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("ANÁLISE DA DISTÂNCIA ENTRE STRIKE E PREÇO DO ATIVO (ITM)")
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
    
    # Análise por faixas de distância
    gerar_analise_faixas_distancia(dados_preparados, output_dir)
    
    # Estatísticas descritivas
    gerar_estatisticas_descritivas(dados_preparados, output_dir)
    
    # Análise estatística avançada
    gerar_analise_estatistica_avancada(dados_preparados, output_dir)
    
    print("\n" + "=" * 80)
    print("ANÁLISE CONCLUÍDA!")
    print("=" * 80)
    print(f"Gráficos salvos em: {output_dir}")
    print("Arquivos gerados:")
    print("- analise_faixas_distancia_itm.png")
    print("- estatisticas_distancia_strike_itm.txt")
    print("- analise_estatistica_avancada_itm.txt")

if __name__ == "__main__":
    main()
