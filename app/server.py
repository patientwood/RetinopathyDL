
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import torch
from pathlib import Path
import logging

from app.model_utils import load_model, predict_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Retinopathy Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device("cpu")
model = None

@app.on_event("startup")
async def startup_event():
    global model
    try:
        logger.info(f"Loading model...")
        model = load_model(device)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.error("Model failed to load")

@app.get("/api/health")
async def health_check():
    model_status = "loaded" if model is not None else "not loaded"
    return {
        "status": "healthy",
        "model_status": model_status
    }

@app.post("/api/predict-image")
async def predict_image_endpoint(file: UploadFile = File(...)):
    if model is None:
        logger.error("Prediction attempted but model is not loaded")
        raise HTTPException(
            status_code = 503,
            detail="Model is not available"
        )
    
    try:
        contents = await file.read()
        result = predict_image(contents, model, device)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

frontend_path = Path("/code/frontend/build")    

if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(str(frontend_path / "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "message": "Backend running. Frontend not built yet.",
            "docs": "/docs",
            "health": "/api/health"
        }