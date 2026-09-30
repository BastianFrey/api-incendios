from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI(title="API de Riesgo de Incendios Valparaíso")

model_path = 'model_artifact/random_forest_v1.joblib'
if os.path.exists(model_path):
    model = joblib.load(model_path)
else:
    model = None

class PredictionInput(BaseModel):
    temperatura: float
    humedad: float
    viento: float

@app.get("/")
def read_root():
    return {"mensaje": "API Activa. Ve a /docs para probar."}

@app.post("/api/v1/predict")
def predict_fire_risk(payload: PredictionInput):
    if model is None:
        return {"error": "Modelo no encontrado. Ejecuta train.py primero."}
    
    df_input = pd.DataFrame([{
        "temperatura": payload.temperatura,
        "humedad": payload.humedad,
        "viento": payload.viento
    }])
    
    riesgo = model.predict(df_input)[0]
    return {"nivel_riesgo": riesgo}