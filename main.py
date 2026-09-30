from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import joblib
import pandas as pd
import os
from supabase import create_client, Client

app = FastAPI(title="API de Riesgo de Incendios Valparaíso")

SUPABASE_URL = os.getenv("SUPABASE_URL", "tu_url_de_supabase")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "tu_api_key_de_supabase")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

model_path = 'model_artifact/random_forest_v1.joblib'
model = joblib.load(model_path) if os.path.exists(model_path) else None

class PredictionInput(BaseModel):
    temperatura: float
    humedad: float
    viento: float
    latitud: float = -33.0456
    longitud: float = -71.6197
    cobertura_vegetal: float = 0.0
    ocurrencia_historica: int = 0

class PredictionOutput(BaseModel):
    nivel_riesgo: str

def log_prediction_supabase(payload: dict, resultado: str):
    try:
        registro = {**payload, "riesgo_predicho": resultado}
        supabase.table("auditoria_predicciones").insert(registro).execute()
    except Exception as e:
        print(f"Error en persistencia: {e}")

@app.post("/api/v1/predict", response_model=PredictionOutput)
async def predict_fire_risk(payload: PredictionInput, background_tasks: BackgroundTasks):
    df_input = pd.DataFrame([{
        "temperatura": payload.temperatura,
        "humedad": payload.humedad,
        "viento": payload.viento
    }])
    
    resultado = model.predict(df_input)[0] if model else "Error: Modelo no cargado"
    
    background_tasks.add_task(log_prediction_supabase, payload.model_dump(), resultado)
    
    return {"nivel_riesgo": resultado}