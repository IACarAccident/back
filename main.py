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
    accident_date: str
    day_of_week: str
    junction_control: str
    junction_detail: str
    light_conditions: str
    speed_limit: int
    road_type: str
    number_of_casualties: int
    road_surface_conditions: str
    urban_or_rural_area: str
    time:str
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
            response = await client.get(f"{IA_SERVICE_URL}/health", timeout=5.0)
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
    try:
        ia_data = {
            "Accident_Date": data.accident_date,
            "Day_of_Week": data.day_of_week,
            "Junction_Control": data.junction_control,
            "Junction_Detail": data.junction_detail,
            "Light_Conditions": data.light_conditions,
            "Speed_limit": data.speed_limit,
            "Road_Type": data.road_type,
            "Number_of_Casualties": data.number_of_casualties,
            "Road_Surface_Conditions": data.road_surface_conditions,
            "Urban_or_Rural_Area": data.urban_or_rural_area,
            "Time": data.time,
            "Weather_Conditions": data.weather_conditions
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
        "accident_date": "3/2/2022",
        "day_of_week": "Tuesday",
        "junction_control": "Give way or uncontrolled",
        "junction_detail": "T or staggered junction",
        "light_conditions": "Daylight",
        "number_of_casualties": 1,
        "road_surface_conditions": "Dry",
        "road_type": "Single carriageway",
        "speed_limit": 30,
        "time": "14:55",
        "urban_or_rural_area": "Urban",
        "weather_conditions": "Fine no high winds"
    }
    logger.info("📋 Données de test créées")
    result = await predict(AccidentData(**test_data))
    logger.info(f"Test réussi: {result}")

    return result