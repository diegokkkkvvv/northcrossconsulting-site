from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

# Ruta del archivo CSV
MASTER_PATH = Path(__file__).parent / "fracciones_industrias.csv"

app = FastAPI(title="North Cross Consulting — Aviso Automático API")

# CORS: permitir peticiones desde tu dominio o cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por ["https://northcrossconsulting.com"] si quieres limitarlo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_master():
    if not MASTER_PATH.exists():
        print(f"⚠️ No se encontró {MASTER_PATH}.")
        return pd.DataFrame(columns=["fraccion", "industria", "aviso_automatico"])
    df = pd.read_csv(MASTER_PATH)
    return df

@app.on_event("startup")
def startup_event():
    global MASTER
    MASTER = load_master()
    print(f"✅ Cargado {len(MASTER)} registros de fracciones arancelarias.")

@app.get("/")
def root():
    return {"message": "North Cross Consulting API is running successfully 🚀"}

@app.get("/consulta")
def consulta(industria: str = Query(...), fraccion: str = Query(...)):
    """Consulta si una fracción requiere aviso automático"""
    fr = fraccion.strip().replace(".", "")
    if len(fr) == 8:
        fr = f"{fr[:4]}.{fr[4:6]}.{fr[6:8]}"

    q = MASTER[(MASTER["fraccion"] == fr) & (MASTER["industria"].str.lower() == industria.lower())]
    if q.empty:
        q2 = MASTER[MASTER["fraccion"] == fr]
        if q2.empty:
            return {"requiere_aviso_automatico": None, "mensaje": "Fracción no encontrada"}
        row = q2.iloc[0]
        return {"requiere_aviso_automatico": bool(row["aviso_automatico"])}

    row = q.iloc[0]
    return {"requiere_aviso_automatico": bool(row["aviso_automatico"])}
