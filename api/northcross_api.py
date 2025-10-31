# api/northcross_api.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
TIGIE_PATH = BASE / "tigie_master.csv"   # cols: fraccion, industria, aviso_automatico
HTS_PATH   = BASE / "hts_master.csv"     # cols: hts10,   industria, aviso_automatico

IND_CANON = {
    "siderurgicos": "Siderurgicos",
    "textil y confeccion": "Textil y Confeccion",
    "textil": "Textil y Confeccion",
    "confeccion": "Textil y Confeccion",
    "calzado": "Calzado",
    "aluminio": "Aluminio",
    "electronica": "Electronica",
    "automotriz": "Automotriz",
    "quimicos": "Quimicos",
}

def canon(s: str) -> str:
    k = (s or "").strip().lower()
    return IND_CANON.get(k, s.strip())

def norm_tigie(code: str) -> str:
    # 0000.00.00 (8 dígitos)
    c = (code or "").replace(".", "").replace(" ", "")
    if len(c) < 8:
        return code.strip()
    c = c[:8]
    return f"{c[:4]}.{c[4:6]}.{c[6:8]}"

def norm_hts(code: str) -> str:
    # 10 dígitos HTSUS
    c = (code or "").replace(".", "").replace(" ", "")
    return c[:10]

def chapter_from_tigie(code: str) -> int | None:
    # capítulo = 2 primeros dígitos del heading de 4
    c = (code or "").replace(".", "")
    if len(c) < 4: 
        return None
    return int(c[:2])

def chapter_from_hts(code10: str) -> int | None:
    c = (code10 or "").replace(".", "")
    if len(c) < 2:
        return None
    return int(c[:2])

def load_overrides(path: Path, cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path, dtype=str).fillna("")
    if "aviso_automatico" in df.columns:
        df["aviso_automatico"] = df["aviso_automatico"].astype(str).str.lower().isin(["1","true","sí","si","yes"])
    return df

def regla_por_capitulo(ch: int, industria: str) -> bool | None:
    ind = (industria or "").strip().lower()
    # Reglas “reales” por sensibilidad histórica de monitoreo (MVP):
    if ch in (72, 73) and ind == "siderurgicos":
        return True
    if 50 <= ch <= 63 and ind in ("textil y confeccion", "textil", "confeccion"):
        return True
    if ch == 64 and ind == "calzado":
        return True
    if ch == 76 and ind == "aluminio":
        return True
    # fuera del scope sensible (o industria no coincide): sin determinación
    return None

app = FastAPI(title="North Cross — Aviso Automático API (MX/USA)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # endurece a tu dominio cuando quieras
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    global DF_TIGIE, DF_HTS
    DF_TIGIE = load_overrides(TIGIE_PATH, ["fraccion", "industria", "aviso_automatico"])
    DF_HTS   = load_overrides(HTS_PATH,   ["hts10",   "industria", "aviso_automatico"])
    print(f"✅ Overrides cargados | TIGIE: {len(DF_TIGIE)} | HTS: {len(DF_HTS)}")

@app.get("/")
def root():
    return {
        "ok": True,
        "datasets": {"tigie": len(DF_TIGIE), "hts": len(DF_HTS)},
        "industries": sorted(set(IND_CANON.values()))
    }

@app.get("/industries")
def industries():
    return {"industries": sorted(set(IND_CANON.values()))}

@app.get("/consulta")
def consulta(
    origin: str = Query(..., description="mx | us"),
    industria: str = Query(...),
    code: str = Query(..., description="TIGIE (mx: 0000.00.00) o HTSUS (us: 10 dígitos)")
):
    ind = canon(industria)
    if origin.lower() == "mx":
        key = norm_tigie(code)
        # 1) Override exacto por CSV
        if not DF_TIGIE.empty:
            q = DF_TIGIE[(DF_TIGIE["fraccion"] == key) & (DF_TIGIE["industria"].str.lower() == ind.lower())]
            if not q.empty:
                return {"origin":"mx","code":key,"industry":ind,"match":"override","requiere_aviso_automatico": bool(q.iloc[0]["aviso_automatico"])}

        # 2) Regla por capítulo
        ch = chapter_from_tigie(key)
        req = regla_por_capitulo(ch, ind) if ch is not None else None
        return {"origin":"mx","code":key,"industry":ind,"match":"rule_chapter","chapter":ch,"requiere_aviso_automatico": req}

    elif origin.lower() == "us":
        key = norm_hts(code)
        # 1) Override exacto por CSV
        if not DF_HTS.empty:
            q = DF_HTS[(DF_HTS["hts10"] == key) & (DF_HTS["industria"].str.lower() == ind.lower())]
            if not q.empty:
                return {"origin":"us","code":key,"industry":ind,"match":"override","requiere_aviso_automatico": bool(q.iloc[0]["aviso_automatico"])}

        # 2) Regla por capítulo (usamos los 2 primeros dígitos del HTS10 → HS capítulo)
        ch = chapter_from_hts(key)
        req = regla_por_capitulo(ch, ind) if ch is not None else None
        return {"origin":"us","code":key,"industry":ind,"match":"rule_chapter","chapter":ch,"requiere_aviso_automatico": req}

    return {"error":"origin inválido: usa 'mx' o 'us'"}
