from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="DataPulse API")

# Add this AFTER creating the app — exposes /metrics endpoint
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {"message": "Welcome to DataPulse API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
