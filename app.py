from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="API de Riesgo de Incendios - Laboratorio Kubernetes")

# 1. Clase de datos con la variable 'vegetacion_seca' solicitada en la guía
class DatosZona(BaseModel):
    temperatura: float
    humedad: float
    viento: float
    vegetacion_seca: bool  

# 2. Endpoint de salud (Health check) que no debe ser modificado
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}

# 3. Endpoint de carga para las pruebas de Autoescalado (HPA) con Minikube
@app.get("/carga")
def generar_carga():
    # Pequeño ciclo para simular consumo de CPU cuando se use el busybox
    x = 0
    for i in range(10000):
        x += i
    return {"status": "ok", "message": "Carga de CPU simulada"}

# 4. Endpoint modificado para calcular el riesgo
@app.post("/riesgo")
def clasificar_riesgo(datos: DatosZona):
    puntos = 0
    
    # Reglas base didácticas (simulando la regla 30-30-30 de su marco teórico)
    if datos.temperatura > 30:
        puntos += 1
    if datos.humedad < 30:
        puntos += 1
    if datos.viento > 30:
        puntos += 1
        
    # NUEVA REGLA: Sumar 1 punto si vegetacion_seca es True
    if datos.vegetacion_seca == True:
        puntos += 1

    # Clasificación exacta solicitada en la Parte C de la guía
    if puntos <= 1:
        nivel_riesgo = "Bajo"
    elif puntos == 2:
        nivel_riesgo = "Medio"
    else:
        nivel_riesgo = "Alto"

    return {
        "puntos_calculados": puntos,
        "clasificacion_riesgo": nivel_riesgo
    }
