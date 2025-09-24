#!/usr/bin/env python3
"""
Programa principal para gerar todos os boxplots das estratégias de Delta Hedge.
Executa os três programas de análise: Delta, Dia e Lote.
"""

import subprocess
import sys
from pathlib import Path

def executar_programa(programa):
    """Executa um programa Python e retorna True se bem-sucedido."""
    try:
        print(f"\n{'='*60}")
        print(f"EXECUTANDO: {programa}")
        print(f"{'='*60}")
        
        # Obter o diretório raiz do projeto (onde está o requirements.txt)
        projeto_root = Path(__file__).parent.parent.parent
        print(f"Diretório de trabalho: {projeto_root}")
        
        resultado = subprocess.run([sys.executable, programa], 
                                 cwd=projeto_root,
                                 check=True)
        
        print(f"✓ {programa} executado com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao executar {programa}:")
        print(f"Código de saída: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado ao executar {programa}: {str(e)}")
        return False

def main():
    """Função principal."""
    print("=" * 80)
    print("GERADOR DE BOXPLOTS - TODAS AS ESTRATÉGIAS DE DELTA HEDGE")
    print("=" * 80)
    
    # Obter o diretório raiz do projeto
    projeto_root = Path(__file__).parent.parent.parent
    print(f"Diretório do projeto: {projeto_root}")
    print(f"Diretório de saída: {projeto_root / 'graficos'}")
    
    # Lista dos programas a serem executados
    programas = [
        'src/gera-graficos/boxplot_simulacao_delta.py',
        'src/gera-graficos/boxplot_simulacao_dia.py', 
        'src/gera-graficos/boxplot_simulacao_lote.py'
    ]
    
    # Verificar se os arquivos existem
    programas_existentes = []
    for programa in programas:
        if Path(programa).exists():
            programas_existentes.append(programa)
        else:
            print(f"⚠️  Arquivo não encontrado: {programa}")
    
    if not programas_existentes:
        print("❌ Nenhum programa encontrado para executar!")
        return
    
    print(f"📊 Encontrados {len(programas_existentes)} programas para executar:")
    for programa in programas_existentes:
        print(f"   - {programa}")
    
    # Executar cada programa
    sucessos = 0
    falhas = 0
    
    for programa in programas_existentes:
        if executar_programa(programa):
            sucessos += 1
        else:
            falhas += 1
    
    # Resumo final
    print(f"\n{'='*80}")
    print("RESUMO DA EXECUÇÃO")
    print(f"{'='*80}")
    print(f"✓ Programas executados com sucesso: {sucessos}")
    print(f"✗ Programas com falha: {falhas}")
    print(f"📁 Gráficos salvos em: {projeto_root / 'graficos'}")
    
    if sucessos > 0:
        print(f"\n📈 Gráficos gerados:")
        print(f"   - Boxplots por categoria de simulação")
        print(f"   - Boxplots por parâmetros específicos de cada estratégia")
        print(f"   - Boxplots combinados")
        print(f"   - Heatmaps de correlação")
        print(f"   - Estatísticas descritivas")
    
    if falhas > 0:
        print(f"\n⚠️  {falhas} programa(s) falharam. Verifique os erros acima.")
        sys.exit(1)
    else:
        print(f"\n🎉 Todos os programas executados com sucesso!")
        print(f"📊 Análise completa das estratégias de Delta Hedge concluída!")

if __name__ == "__main__":
    main()
