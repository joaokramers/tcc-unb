import pandas as pd
import re
from pathlib import Path
import glob
import os

def convert_txt_to_csv(txt_path: str):
    in_path = Path(txt_path)
    out_path = in_path.with_suffix(".csv")

    try:
        # Ler arquivo ignorando cabeçalho
        df = pd.read_csv(in_path, delim_whitespace=True, skiprows=1, header=None)

        # Renomear colunas
        df.columns = ["Data", "Var%", "Var", "Cotação", "Abertura", "Mínimo", "Máximo", "Volume", "Nº Negócios"]

        # Selecionar colunas relevantes
        df_sel = df[["Data", "Abertura", "Máximo", "Mínimo", "Cotação", "Nº Negócios", "Volume"]].copy()

        # Converter data para yyyy.mm.dd
        df_sel["Data"] = pd.to_datetime(df_sel["Data"], format="%d/%m/%Y").dt.strftime("%Y.%m.%d")

        # Funções auxiliares
        def parse_num(s):
            if pd.isna(s):
                return None
            s = str(s).replace(".", "").replace(",", ".")
            try:
                return float(s)
            except ValueError:
                return None

        def parse_int_with_k(s):
            if pd.isna(s):
                return None
            s = str(s).upper().strip()
            if s.endswith("K"):
                return int(float(s[:-1].replace(",", ".")) * 1000)
            try:
                return int(s.replace(".", "").replace(",", ""))
            except ValueError:
                return None

        # Aplicar conversões
        df_sel["Abertura"] = df_sel["Abertura"].map(parse_num)
        df_sel["Máximo"] = df_sel["Máximo"].map(parse_num)
        df_sel["Mínimo"] = df_sel["Mínimo"].map(parse_num)
        df_sel["Cotação"] = df_sel["Cotação"].map(parse_num)
        df_sel["Nº Negócios"] = df_sel["Nº Negócios"].map(parse_int_with_k)
        df_sel["Volume"] = df_sel["Volume"].map(parse_int_with_k)

        # Salvar CSV sem cabeçalho
        df_sel.to_csv(out_path, index=False, header=False)
        print(f"✓ Arquivo CSV gerado: {out_path}")
        return True

    except Exception as e:
        print(f"✗ Erro ao processar {txt_path}: {str(e)}")
        return False

def convert_all_petr_files(dados_dir: str = "dados"):
    """
    Converte todos os arquivos PETR*.txt para CSV no diretório especificado
    """
    # Buscar todos os arquivos PETR*.txt (incluindo séries E, F, G, H, I, J)
    pattern = os.path.join(dados_dir, "PETR*.txt")
    txt_files = glob.glob(pattern)
    
    if not txt_files:
        print(f"Nenhum arquivo PETR*.txt encontrado em {dados_dir}")
        return
    
    print(f"Encontrados {len(txt_files)} arquivos PETR*.txt para converter:")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    
    for txt_file in sorted(txt_files):
        print(f"Processando: {os.path.basename(txt_file)}")
        if convert_txt_to_csv(txt_file):
            success_count += 1
        else:
            error_count += 1
    
    print("-" * 50)
    print(f"Conversão concluída!")
    print(f"✓ Sucessos: {success_count}")
    print(f"✗ Erros: {error_count}")
    print(f"Total processados: {len(txt_files)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Modo individual: converter arquivo específico
        convert_txt_to_csv(sys.argv[1])
    else:
        # Modo lote: converter todos os arquivos PETR*.txt
        convert_all_petr_files()
