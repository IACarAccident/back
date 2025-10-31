from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import logging
import httpx

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IA_SERVER_URL = "http://ia-service:8080"

class AccidentData(BaseModel):
    day_of_week: str
    junction_control: str
    junction_detail: str
    light_conditions: str
    road_surface_conditions: str
    road_type: str
    speed_limit: int
    urban_or_rural_area: str
    weather_conditions: str

class PredictionResult(BaseModel):
    prediction: str
    probability: Dict[str, float]
    confidence: float

@app.get("/")
def read_root():
    return {"message": "Backend Accidents - API"}


@app.get("/health")
async def health_check():
    try:
        logger.info("🔍 Vérification santé IA...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{IA_SERVER_URL}/health", timeout=5.0)
            ia_health = response.json()

        logger.info(f"IA santé: {ia_health}")
        return {
            "backend": "healthy",
            "ia_service": ia_health,
            "status": "all_services_ok"
        }
    except Exception as e:
        logger.error(f"IA inaccessible: {e}")
        return {
            "backend": "healthy",
            "ia_service": "unreachable",
            "error": str(e)
        }
@app.post("/api/predict")
async def predict(data: dict):
    print(data)
    try:
        ia_data = {
            "day_of_week": data['day_of_week'],
            "junction_control": data['junction_control'],
            "junction_detail": data['junction_detail'],
            "light_conditions": data['light_conditions'],
            "road_surface_conditions": data['road_surface_conditions'],
            "road_type": data['road_type'],
            "speed_limit": data['speed_limit'],
            "urban_or_rural_area": data['urban_or_rural_area'],
            "weather_conditions": data['weather_conditions']
        }

        print(f"Données reçues: {ia_data}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{IA_SERVER_URL}/predict",
                json=ia_data,
                timeout=30.0
            )

            if response.status_code == 200:
                ia_result = response.json()
                print(f"Réponse de l'IA: {ia_result}")

                return PredictionResult(
                    prediction=ia_result["prediction"],
                    probability=ia_result["probability"],
                    confidence=ia_result["confidence"]
                )
            else:
                error_detail = f"Erreur IA {response.status_code}: {response.text}"
                print(f"❌ Erreur détaillée: {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erreur IA: {response.text}"
                )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code = 503,
            detail=f"Service IA indisponible: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail=f"Erreur interne: {str(e)}"
        )


@app.get("/api/test-prediction")
async def test_prediction():
    """Route de test pour vérifier la connexion à l'IA"""
    logger.info("Test prédiction démarré")

    test_data = {
        "day_of_week": "Tuesday",
        "junction_control": "Give way or uncontrolled",
        "junction_detail": "T or staggered junction",
        "light_conditions": "Daylight",
        "road_surface_conditions": "Dry",
        "road_type": "Single carriageway",
        "speed_limit": 30,
        "urban_or_rural_area": "Urban",
        "weather_conditions": "Fine no high winds"
    }
    logger.info("📋 Données de test créées")
    result = await predict(test_data)
    logger.info(f"Test réussi: {result}")

    return result