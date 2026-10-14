import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Inicialización del API Gateway
app = FastAPI(
    title="Sistema de Monitoreo de Riesgo de Incendios - Región de Valparaíso",
    description="API Gateway y Microservicios para la evaluación geoespacial de riesgo de incendios forestales.",
    version="1.0.0"
)

# Configuración CORS para conexión con Frontend (Leaflet.js / React / Vue)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# CARGA DEL MODELO (Inference Engine / Singleton)
# -----------------------------------------------------------------------------
MODEL_PATH = os.path.join("model_artifact", "random_forest_v1.joblib")
model = None

if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print(f"✅ Modelo de IA cargado exitosamente desde {MODEL_PATH}")
    except Exception as e:
        print(f"⚠️ Error al cargar el modelo: {e}. Se utilizará motor de reglas de respaldo.")
else:
    print(f"⚠️ No se encontró {MODEL_PATH}. Usando motor de respaldo.")


# -----------------------------------------------------------------------------
# ESQUEMAS DE DATOS (Pydantic Models)
# -----------------------------------------------------------------------------
class DatosClimaticosEntrada(BaseModel):
    comuna: str = Field(..., example="Valparaíso")
    temperatura: float = Field(..., ge=-10, le=60, description="Temperatura en °C")
    humedad: float = Field(..., ge=0, le=100, description="Humedad relativa %")
    viento: float = Field(..., ge=0, le=150, description="Velocidad del viento en km/h")
    cobertura_vegetal: float = Field(default=75.0, ge=0, le=100, description="Índice de cobertura vegetal %")
    historial_incendios: int = Field(default=5, ge=0, description="Cantidad de incendios previa en la zona")

class RespuestaRiesgo(BaseModel):
    comuna: str
    nivel_riesgo: str
    probabilidad_alto_riesgo: float
    condicion_30_30_30: bool
    fuente_evaluacion: str


# -----------------------------------------------------------------------------
# MICROSERVICIO 1: SERVICIO DE DATOS TERRITORIALES Y CLIMÁTICOS (Mock Data)
# -----------------------------------------------------------------------------
# Base de datos simulada de comunas de la Región de Valparaíso
MOCK_COMMUNES_DATA = {
    "valparaiso": {
        "comuna": "Valparaíso",
        "temperatura": 32.5,
        "humedad": 25.0,
        "viento": 35.0,
        "cobertura_vegetal": 80.0,
        "historial_incendios": 12,
        "fuente": "IDE Chile / CONAF / API Meteorológica (Mock)"
    },
    "vina_del_mar": {
        "comuna": "Viña del Mar",
        "temperatura": 29.0,
        "humedad": 35.0,
        "viento": 22.0,
        "cobertura_vegetal": 65.0,
        "historial_incendios": 8,
        "fuente": "IDE Chile / CONAF / API Meteorológica (Mock)"
    },
    "quilpue": {
        "comuna": "Quilpué",
        "temperatura": 34.0,
        "humedad": 20.0,
        "viento": 31.0,
        "cobertura_vegetal": 85.0,
        "historial_incendios": 15,
        "fuente": "IDE Chile / CONAF / API Meteorológica (Mock)"
    },
    "villa_alemana": {
        "comuna": "Villa Alemana",
        "temperatura": 33.0,
        "humedad": 22.0,
        "viento": 28.0,
        "cobertura_vegetal": 70.0,
        "historial_incendios": 6,
        "fuente": "IDE Chile / CONAF / API Meteorológica (Mock)"
    }
}

@app.get("/api/v1/datos/{comuna_id}", tags=["Microservicio Datos"])
def obtener_datos_territoriales(comuna_id: str):
    """
    Simula la ingesta de datos desde IDE Chile, CONAF y API Meteorológica externa.
    """
    key = comuna_id.lower().replace(" ", "_")
    if key in MOCK_COMMUNES_DATA:
        return MOCK_COMMUNES_DATA[key]
    
    # Respuesta por defecto si la comuna no está registrada explícitamente
    return {
        "comuna": comuna_id.capitalize(),
        "temperatura": 28.0,
        "humedad": 40.0,
        "viento": 18.0,
        "cobertura_vegetal": 50.0,
        "historial_incendios": 3,
        "fuente": "IDE Chile / CONAF / API Meteorológica (Mock Generico)"
    }


# -----------------------------------------------------------------------------
# MICROSERVICIO 2: SERVICIO DE EVALUACIÓN DE RIESGO (Inference Engine)
# -----------------------------------------------------------------------------
@app.post("/api/v1/riesgo/evaluar", response_model=RespuestaRiesgo, tags=["Microservicio Riesgo"])
def evaluar_riesgo(datos: DatosClimaticosEntrada):
    """
    Procesa las variables climáticas y de cobertura vegetal con el modelo Random Forest.
    """
    # Verificación Regla 30-30-30 (Temp >= 30°C, Humedad <= 30%, Viento >= 30 km/h)
    es_30_30_30 = (datos.temperatura >= 30.0) and (datos.humedad <= 30.0) and (datos.viento >= 30.0)

    # Evaluación mediante modelo Scikit-Learn
    if model is not None:
        try:
            input_df = pd.DataFrame([{
                "temperatura": datos.temperatura,
                "humedad": datos.humedad,
                "viento": datos.viento,
                "cobertura_vegetal": datos.cobertura_vegetal,
                "historial_incendios": datos.historial_incendios
            }])
            
            prediccion = model.predict(input_df)[0]
            probabilidades = model.predict_proba(input_df)[0]
            prob_alto = round(float(probabilidades[-1]) * 100, 2)
            
            # Map de clase predicha a etiqueta
            etiquetas = {0: "Bajo", 1: "Medio", 2: "Alto"}
            nivel = etiquetas.get(int(prediccion), "Alto" if es_30_30_30 else "Moderado")
            
            return RespuestaRiesgo(
                comuna=datos.comuna,
                nivel_riesgo=nivel,
                probabilidad_alto_riesgo=prob_alto,
                condicion_30_30_30=es_30_30_30,
                fuente_evaluacion="Inference Engine (Random Forest ML)"
            )
        except Exception as e:
            print(f"Error durante inferencia de modelo: {e}")

    # Fallback / Reglas deterministas si el modelo no está disponible
    nivel_fallback = "Alto" if es_30_30_30 else ("Medio" if datos.temperatura > 25 else "Bajo")
    prob_fallback = 88.5 if es_30_30_30 else (52.0 if datos.temperatura > 25 else 15.0)

    return RespuestaRiesgo(
        comuna=datos.comuna,
        nivel_riesgo=nivel_fallback,
        probabilidad_alto_riesgo=prob_fallback,
        condicion_30_30_30=es_30_30_30,
        fuente_evaluacion="Motor de Reglas Determinista (Fallback 30-30-30)"
    )


# -----------------------------------------------------------------------------
# API GATEWAY (Ruta Principal / Healthcheck)
# -----------------------------------------------------------------------------
@app.get("/", tags=["API Gateway"])
def gateway_healthcheck():
    return {
        "servicio": "API Gateway - Monitoreo de Riesgo de Incendios",
        "estado": "Operativo",
        "region": "Valparaíso, Chile",
        "endpoints_disponibles": {
            "datos_comunales": "/api/v1/datos/{comuna_id}",
            "evaluacion_riesgo": "/api/v1/riesgo/evaluar",
            "documentacion_interactive": "/docs"
        }
    }

