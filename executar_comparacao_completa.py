#!/usr/bin/env python3
"""
Script para executar análise completa de comparação de preços de opções.
Executa todos os programas na ordem correta.
"""

import subprocess
import sys
import os

def executar_comando(descricao, comando):
    """Executa um comando e exibe o resultado."""
    print("\n" + "="*80)
    print(f"📊 {descricao}")
    print("="*80)
    
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✅ {descricao} - CONCLUÍDO")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERRO: {descricao} falhou")
        print(f"Código de erro: {e.returncode}")
        return False

def main():
    """Função principal."""
    print("\n" + "#"*80)
    print("# ANÁLISE COMPLETA DE COMPARAÇÃO DE PREÇOS DE OPÇÕES")
    print("# Opções: PETRI28 (ITM), PETRI333 (OTM), PETRH369 (OTM Profundo)")
    print("#"*80)
    
    # Verifica se está no diretório correto
    if not os.path.exists("banco/mercado_opcoes.db"):
        print("\n❌ ERRO: Banco de dados não encontrado!")
        print("Execute este script do diretório raiz do projeto (C:\\Unb\\tcc-unb)")
        sys.exit(1)
    
    print("\n📂 Diretório de trabalho:", os.getcwd())
    print("✅ Banco de dados encontrado")
    
    # Menu de opções
    print("\n" + "="*80)
    print("ESCOLHA O TIPO DE ANÁLISE:")
    print("="*80)
    print("1. Análise COMPLETA (3 opções: ITM, OTM, OTM Profundo)")
    print("2. Análise de UMA opção específica")
    print("3. Executar TUDO (análises individuais + consolidado)")
    print("="*80)
    
    escolha = input("\nDigite sua escolha (1, 2 ou 3): ").strip()
    
    if escolha == "1":
        # Análise completa das 3 opções
        print("\n🎯 Executando análise completa das 3 opções...")
        
        sucesso = executar_comando(
            "Relatório Consolidado ITM/ATM/OTM",
            "python src/precos/RelatorioFinal_ITM_ATM_OTM.py"
        )
        
        if sucesso:
            print("\n" + "="*80)
            print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print("\n📁 Arquivos gerados:")
            print("  - dados-comparacao-preco/relatorio_final_ITM_ATM_OTM.csv")
            print("\n💡 Verifique o terminal acima para ver os resultados detalhados.")
        
    elif escolha == "2":
        # Análise de uma opção específica
        print("\n" + "="*80)
        print("OPÇÕES DISPONÍVEIS:")
        print("="*80)
        print("1. PETRI28 (ITM, Delta 0.82) - ID Simulação: 29")
        print("2. PETRI333 (OTM Borderline, Delta 0.28) - ID Simulação: 32")
        print("3. PETRH369 (OTM Profundo, Delta 0.05) - ID Simulação: 27")
        print("="*80)
        
        opcao = input("\nQual opção deseja analisar? (1, 2 ou 3): ").strip()
        
        ids_map = {"1": 29, "2": 32, "3": 27}
        nomes_map = {"1": "PETRI28", "2": "PETRI333", "3": "PETRH369"}
        
        if opcao in ids_map:
            id_sim = ids_map[opcao]
            nome = nomes_map[opcao]
            
            print(f"\n⚠️  ATENÇÃO: Você precisa editar manualmente o arquivo:")
            print(f"    src/precos/ComparadorPrecosOpcoes.py")
            print(f"    Linha 13: ID_SIMULACAO = {id_sim}")
            print(f"\nDepois execute:")
            print(f"    python src/precos/ComparadorPrecosOpcoes.py")
        else:
            print("❌ Opção inválida!")
    
    elif escolha == "3":
        # Executar tudo
        print("\n🎯 Executando TODAS as análises...")
        
        # 1. Análise individual de cada opção
        sucesso1 = executar_comando(
            "Análise Individual das 3 Opções",
            "python src/precos/AnalisarOpcoes_ITM_ATM_OTM.py"
        )
        
        # 2. Relatório consolidado
        sucesso2 = executar_comando(
            "Relatório Consolidado Final",
            "python src/precos/RelatorioFinal_ITM_ATM_OTM.py"
        )
        
        if sucesso1 and sucesso2:
            print("\n" + "="*80)
            print("✅ TODAS AS ANÁLISES CONCLUÍDAS COM SUCESSO!")
            print("="*80)
            print("\n📁 Arquivos gerados:")
            print("  - dados-comparacao-preco/resumo_PETRI28.csv")
            print("  - dados-comparacao-preco/resumo_PETRI313.csv")
            print("  - dados-comparacao-preco/resumo_PETRH369.csv")
            print("  - dados-comparacao-preco/resumo_ITM_ATM_OTM.csv")
            print("  - dados-comparacao-preco/relatorio_final_ITM_ATM_OTM.csv")
            print("\n💡 Todos os dados estão prontos para análise!")
    
    else:
        print("❌ Escolha inválida!")
        sys.exit(1)
    
    print("\n" + "#"*80)
    print("# FIM DA EXECUÇÃO")
    print("#"*80 + "\n")

if __name__ == "__main__":
    main()

