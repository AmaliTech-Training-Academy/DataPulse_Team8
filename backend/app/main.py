from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.database import Base, engine
from app.middleware.logging_middleware import GlobalLoggingMiddleware
from app.routers import auth, checks, reports, rules, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    import app.models.check_result  # noqa: F401
    import app.models.dataset  # noqa: F401
    import app.models.rule  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="DataPulse",
    description="Data Quality Monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# Initialize and expose Prometheus metrics
Instrumentator().instrument(app).expose(app)

app.add_middleware(GlobalLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(upload.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(rules.router, prefix="/api/rules", tags=["Rules"])
app.include_router(checks.router, prefix="/api/checks", tags=["Checks"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


@app.get("/")
def root():
    return {"name": "DataPulse", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
