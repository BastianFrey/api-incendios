FROM python:3.11-slim

WORKDIR /app

# Copiar requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del repositorio
COPY . .

# Exponer el puerto
EXPOSE 8000

# Comando de inicio de la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]