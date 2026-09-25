# app/main.py
from contextlib import asynccontextmanager
from pathlib import Path
import os
import logging

import joblib  # <-- Make sure this import is here
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from app.core.config import get_settings
from app.core.db import Base, async_engine
from app.api.v1.endpoints.transactions import router as transactions_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.dataset import router as dataset_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.entities import router as entities_router
from app.api.v1.endpoints.tables import router as tables_router
from app.api.v1.endpoints.training import router as training_router
from app.services.fraud_engine import fraud_engine

# -------------------- logging (module-level, once) --------------------
logger = logging.getLogger("fortix")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)
# ---------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App startup/shutdown.
    """
    # Auto-create database tables on startup
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ---- Load fraud model on startup ----
    model_path = os.getenv("MODEL_PATH", str(Path("ml_models") / "fraud_model.joblib"))
    logger.info("Attempting to load model from %s", model_path)
    try:
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load the model pipeline directly using joblib
        model_pipeline = joblib.load(model_path)
        
        # Store the loaded model directly onto the fraud_engine service
        fraud_engine.model = model_pipeline
        
        # Log success with the class name of the loaded pipeline
        cls = fraud_engine.model.__class__.__name__
        logger.info("✅ ML model loaded successfully: %s", cls)

    except Exception:
        logger.exception("❌ Failed to load the model; rules-only mode will be used.")

    # ---- Load feature importances on startup ----
    fi_path = Path(os.getenv("FEATURE_IMPORTANCE_PATH", str(Path("ml_models") / "feature_importance.csv")))
    logger.info("Attempting to load feature importances from %s", fi_path)
    try:
        if fi_path.exists():
            df = pd.read_csv(fi_path)
            items = df.to_dict(orient="records")
            fraud_engine.feature_importances = items
            logger.info("✅ Feature importances loaded: %d features", len(items))
        else:
            logger.warning("Feature importance file not found: %s", fi_path)
    except Exception:
        logger.exception("❌ Failed to load feature importances")

    yield
    # (Optional) add shutdown cleanup here


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Routers
    application.include_router(transactions_router, prefix="/api/v1", tags=["transactions"])
    application.include_router(dashboard_router,    prefix="/api/dashboard", tags=["dashboard"])
    application.include_router(dataset_router,      prefix="/api/dataset",   tags=["dataset"])
    application.include_router(analytics_router,    prefix="/api/analytics", tags=["analytics"])
    application.include_router(entities_router,     prefix="/api",           tags=["entities"])
    application.include_router(tables_router,       prefix="/api/tables",    tags=["tables"])
    application.include_router(training_router,     prefix="/api/training",  tags=["training"])

    @application.get("/")
    async def root():
        return {"service": settings.APP_NAME, "status": "ok"}

    @application.get("/_debug/model")
    async def debug_model(request: Request):
        model_obj = getattr(fraud_engine, "model", None)
        cls = getattr(model_obj, "__class__", type(model_obj)).__name__ if model_obj else None
        return {
            "loaded": model_obj is not None,
            "path": os.getenv("MODEL_PATH", str(Path("ml_models") / "fraud_model.joblib")),
            "class": cls,
        }

    return application


# This is the ONLY app instance uvicorn should use.
app = create_app()