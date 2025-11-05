# ==============================
# North Cross – FastAPI backend
# ==============================
import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd

# ---- Config ----
# Limit CORS to your production domains (comma-separated env supports previews if needed)
DEFAULT_ORIGINS = [
    "https://www.northcrossconsulting.com",
    "https://northcrossconsulting-site.github.io"  # if you ever preview on GH Pages
]
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", ",".join(DEFAULT_ORIGINS)).split(",") if o.strip()
]

app = FastAPI(title="North Cross API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---- Load data once at boot ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _csv(path):
    return os.path.join(BASE_DIR, path)

try:
    tigie_df = pd.read_csv(_csv("tigie_master.csv"), dtype=str).fillna("")
except Exception as e:
    tigie_df = pd.DataFrame()
    print("WARN: tigie_master.csv not loaded:", e)

try:
    hts_df = pd.read_csv(_csv("hts_master.csv"), dtype=str).fillna("")
except Exception as e:
    hts_df = pd.DataFrame()
    print("WARN: hts_master.csv not loaded:", e)

# Optional supporting file for future logic; safe if missing
try:
    fracciones_ind = pd.read_csv(_csv("fracciones_industrias.csv"), dtype=str).fillna("")
except Exception:
    fracciones_ind = pd.DataFrame()

def norm_code(code: str) -> str:
    if not code:
        return ""
    s = str(code).strip()
    s = s.replace(" ", "")
    # keep dots as provided
    return s

def match_override(df: pd.DataFrame, code_col: str, code: str):
    if df.empty or code_col not in df.columns:
        return None
    # exact match first
    row = df.loc[df[code_col].str.strip().eq(code)]
    if not row.empty:
        return row.iloc[0].to_dict()
    # prefix (chapter) match if you keep chapter column e.g. 'capitulo'
    chap_col = "capitulo" if "capitulo" in df.columns else None
    if chap_col:
        chapter = code.split(".")[0] if "." in code else code[:2]
        row = df.loc[df[chap_col].astype(str).str.zfill(2).eq(str(chapter).zfill(2))]
        if not row.empty:
            return row.iloc[0].to_dict()
    return None

@app.get("/health")
def health():
    return {"status": "ok", "origins": ALLOWED_ORIGINS}

@app.get("/consulta")
def consulta(
    origin: str = Query(..., pattern="^(mx|us)$"),
    industria: str = Query(..., min_length=2),
    code: str = Query(..., min_length=4)
):
    """Main decision endpoint."""
    code_n = norm_code(code)
    origin = origin.lower()

    if origin == "mx":
        if tigie_df.empty:
            return JSONResponse({"mensaje": "Base TIGIE no disponible", "requiere_aviso_automatico": None}, status_code=503)
        row = match_override(tigie_df, "fraccion", code_n) or match_override(tigie_df, "codigo", code_n)
    else:
        if hts_df.empty:
            return JSONResponse({"mensaje": "Base HTSUS no disponible", "requiere_aviso_automatico": None}, status_code=503)
        row = match_override(hts_df, "htsus", code_n) or match_override(hts_df, "codigo", code_n)

    if not row:
        return {"mensaje": "Fracción no encontrada", "requiere_aviso_automatico": None}

    # Expected column naming (adjust if your CSVs differ)
    # Looking for any truthy indicator in these typical columns:
    flags = [
        "requiere_aviso_automatico",
        "aviso_automatico",
        "requiere_aviso",
        "requiere",
        "requiere_aviso_boolean"
    ]
    requiere = None
    for f in flags:
        if f in row:
            val = str(row[f]).strip().lower()
            if val in ("true", "1", "sí", "si", "yes"):
                requiere = True
            elif val in ("false", "0", "no", ""):
                requiere = False
            if requiere is not None:
                break

    payload = {
        "requiere_aviso_automatico": requiere,
        "industria": industria,
        "origin": origin,
        "code": code_n,
        "match_source": "override/prefix",
    }
    if "descripcion" in row:
        payload["descripcion"] = row["descripcion"]

    return payload
