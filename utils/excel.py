"""utils/excel.py — Leitura + detecção automática de cidade pelo endereço"""
import pandas as pd, io, re

COLS = ["CNPJ","Razão Social","Ramo de Atividade","Endereço","Telefone","Email"]


def extrair_cidade(endereco):
    """Extrai cidade de endereços no padrão: 'Rua X, 100 - Bairro, Cidade - UF, CEP'"""
    if not isinstance(endereco, str) or not endereco.strip():
        return None
    # Padrão principal: ", Cidade - UF,"
    m = re.search(r',\s*([^,]+?)\s*-\s*[A-Z]{2}(?:,|\s+\d{5})', endereco)
    if m:
        return m.group(1).strip()
    # Fallback: última cidade antes de " - UF"
    m2 = re.search(r',\s*([^,\-]+?)\s*-\s*[A-Z]{2}', endereco)
    if m2:
        return m2.group(1).strip()
    return None


def extrair_estado(endereco):
    """Extrai UF do endereço."""
    if not isinstance(endereco, str):
        return None
    m = re.search(r'-\s*([A-Z]{2})(?:,|\s+\d{5})', endereco)
    return m.group(1) if m else None


def ler(arquivo):
    try:
        df = pd.read_csv(arquivo, dtype=str) if arquivo.name.endswith(".csv") \
             else pd.read_excel(arquivo, dtype=str)
    except Exception as e:
        return None, str(e)

    # Normaliza nomes de colunas (remove espaços e padroniza capitalização)
    mapa_cols = {
        "cnpj":               "CNPJ",
        "razão social":       "Razão Social",
        "razao social":       "Razão Social",
        "ramo de atividade":  "Ramo de Atividade",
        "ramo":               "Ramo de Atividade",
        "endereço":           "Endereço",
        "endereco":           "Endereço",
        "telefone":           "Telefone",
        "email":              "Email",
        "e-mail":             "Email",
    }
    df.columns = [mapa_cols.get(c.strip().lower(), c.strip()) for c in df.columns]

    if "Razão Social" not in df.columns:
        return None, "Coluna 'Razão Social' não encontrada."

    for c in COLS:
        if c not in df.columns:
            df[c] = None

    df = df.dropna(how="all").reset_index(drop=True)

    for c in df.select_dtypes("object").columns:
        df[c] = df[c].astype(str).str.strip().replace({"nan": None, "None": None, "": None})

    # Detecção automática
    df["_cidade"] = df["Endereço"].apply(extrair_cidade)
    df["_estado"] = df["Endereço"].apply(extrair_estado)

    return df, None


def template():
    df = pd.DataFrame(columns=COLS)
    df.loc[0] = ["00.000.000/0001-00", "Empresa Exemplo Ltda", "Comércio",
                 "Rua X, 100 - Centro, São Paulo - SP, 01310-000",
                 "(11)99999-9999", "email@empresa.com"]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False)
        fmt = w.book.add_format({"bold": True, "bg_color": "#041747", "font_color": "#FAC319"})
        ws = w.sheets["Sheet1"]
        for i, c in enumerate(COLS):
            ws.write(0, i, c, fmt)
            ws.set_column(i, i, 28)
    return buf.getvalue()
