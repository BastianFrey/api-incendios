import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

data = {
    'temperatura': [20, 35, 15, 40, 25],
    'humedad': [60, 20, 80, 15, 50],
    'viento': [10, 40, 5, 50, 15],
    'riesgo': ['Bajo', 'Alto', 'Bajo', 'Alto', 'Medio']
}
df = pd.DataFrame(data)

X = df[['temperatura', 'humedad', 'viento']]
y = df['riesgo']

print("Entrenando modelo Random Forest...")
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X, y)

os.makedirs('model_artifact', exist_ok=True)
joblib.dump(clf, 'model_artifact/random_forest_v1.joblib')
print("¡Modelo guardado con éxito en model_artifact/random_forest_v1.joblib!")