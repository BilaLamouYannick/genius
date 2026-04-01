"""
═══════════════════════════════════════════════════════════════════
 GENIUS — API FastAPI — Prédiction Qualité de l'Air au Cameroun
 Hackathon IndabaX Cameroon 2026
═══════════════════════════════════════════════════════════════════
 Lancement :  uvicorn main:app --reload --port 8000
 Docs      :  http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import pickle, math, numpy as np, os, json
from datetime import date

# ── Chargement du modèle ──────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'xgboost_pm25_genius.pkl')
META_PATH  = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_metadata.json')

try:
    with open(MODEL_PATH, 'rb') as f:
        ARTIFACTS = pickle.load(f)
    with open(META_PATH, 'r', encoding='utf-8') as f:
        METADATA = json.load(f)
    print(f"✅ Modèle chargé — R² = {ARTIFACTS['model_metrics']['r2']:.4f}")
except FileNotFoundError:
    raise RuntimeError(
        "❌ Modèle introuvable. Exécuter d'abord la section 9 du notebook "
        "pour générer 'models/xgboost_pm25_genius.pkl'"
    )

# ── Application FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title       = "GENIUS — Air Quality API",
    description = "API de prédiction de la qualité de l'air au Cameroun "
                  "— Hackathon IndabaX Cameroon 2026 — Équipe GENIUS",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# ── Schémas Pydantic ──────────────────────────────────────────────────────────
class MeteoInput(BaseModel):
    city                        : str   = Field(..., example="Maroua")
    region                      : str   = Field(..., example="Extreme-Nord")
    date                        : str   = Field(..., example="2025-01-15")
    temperature_2m_mean         : float = Field(..., example=34.0)
    temperature_2m_max          : float = Field(..., example=40.0)
    temperature_2m_min          : float = Field(..., example=28.0)
    precipitation_sum           : float = Field(..., example=0.0)
    precipitation_hours         : float = Field(0.0, example=0.0)
    wind_speed_10m_max          : float = Field(..., example=3.5)
    shortwave_radiation_sum     : float = Field(..., example=22.0)
    sunshine_duration           : float = Field(..., example=35000.0)
    et0_fao_evapotranspiration  : float = Field(..., example=6.5)
    daylight_duration           : float = Field(43200.0, example=43200.0)
    latitude                    : float = Field(..., example=10.59)
    longitude                   : float = Field(..., example=14.32)
    # Lags (optionnels — remplacés par des valeurs par défaut si absents)
    temp_lag1   : Optional[float] = None
    temp_lag7   : Optional[float] = None
    wind_lag1   : Optional[float] = None
    rain_lag1   : Optional[float] = None
    rain_lag7   : Optional[float] = None
    temp_roll7  : Optional[float] = None
    wind_roll7  : Optional[float] = None
    rain_roll7  : Optional[float] = None


class PredictionResponse(BaseModel):
    ville       : str
    region      : str
    date        : str
    pm25_proxy  : float
    niveau      : str
    couleur     : str
    emoji       : str
    conseil     : str
    details     : dict


class BatchInput(BaseModel):
    observations: list[MeteoInput]


# ── Logique de prédiction ─────────────────────────────────────────────────────
def _compute_features(data: dict) -> dict:
    """Calcule toutes les features dérivées à partir des données météo brutes."""
    d = data.copy()

    # Parse date
    d_date       = date.fromisoformat(d['date'])
    d['month']   = d_date.month
    d['day_of_year'] = d_date.timetuple().tm_yday
    d['quarter'] = (d['month'] - 1) // 3 + 1

    # Features dérivées
    d['temp_amplitude']  = d['temperature_2m_max'] - d['temperature_2m_min']
    d['sunshine_ratio']  = min(max(
        d['sunshine_duration'] / (d['daylight_duration'] + 1e-6), 0), 1)
    d['is_no_wind']      = int(d['wind_speed_10m_max'] < 5)
    d['is_low_wind']     = int(d['wind_speed_10m_max'] < 10)
    d['is_no_rain']      = int(d['precipitation_sum'] < 0.1)
    d['is_dry_season']   = int(d['month'] in [11, 12, 1, 2, 3])
    d['stagnation_score']= min(d['is_no_wind']*3 + d['is_no_rain']*2 + d['is_dry_season'], 6)

    # Encodage cyclique
    d['month_sin'] = math.sin(2 * math.pi * d['month'] / 12)
    d['month_cos'] = math.cos(2 * math.pi * d['month'] / 12)
    d['doy_sin']   = math.sin(2 * math.pi * d['day_of_year'] / 365)
    d['doy_cos']   = math.cos(2 * math.pi * d['day_of_year'] / 365)

    # Encodage région / ville
    try:
        d['region_enc'] = int(ARTIFACTS['le_region'].transform([d['region']])[0])
    except ValueError:
        raise HTTPException(422, f"Région inconnue : '{d['region']}'. "
                            f"Régions valides : {ARTIFACTS['le_region'].classes_.tolist()}")
    try:
        d['city_enc'] = int(ARTIFACTS['le_city'].transform([d['city']])[0])
    except ValueError:
        raise HTTPException(422, f"Ville inconnue : '{d['city']}'. "
                            f"Villes valides : {ARTIFACTS['le_city'].classes_.tolist()}")

    # Lags — valeurs par défaut si non fournis
    for lag_col in ['temp_lag1','temp_lag7','wind_lag1','rain_lag1','rain_lag7',
                    'temp_roll7','wind_roll7','rain_roll7']:
        if d.get(lag_col) is None:
            # Défaut : valeur courante (approximation raisonnable)
            if 'temp' in lag_col:
                d[lag_col] = d['temperature_2m_mean']
            elif 'wind' in lag_col:
                d[lag_col] = d['wind_speed_10m_max']
            else:
                d[lag_col] = d['precipitation_sum']
    return d


def _get_alert(pm: float) -> tuple[str, str, str, str]:
    if pm < 20:    return 'Bon',       '#27AE60', '🟢', "Qualité de l'air satisfaisante. Activités extérieures sans restriction."
    elif pm < 35:  return 'Modéré',    '#F39C12', '🟡', "Qualité acceptable. Personnes sensibles : limiter les efforts physiques."
    elif pm < 50:  return 'Mauvais',   '#E67E22', '🟠', "Population sensible affectée. Éviter activités physiques intenses."
    else:          return 'Dangereux', '#E74C3C', '🔴', "Alerte rouge ! Rester à l'intérieur. Consultation médicale conseillée."


def _predict_one(obs: MeteoInput) -> dict:
    d  = _compute_features(obs.model_dump())
    X  = np.array([[d[f] for f in ARTIFACTS['features']]])
    pm = float(ARTIFACTS['model'].predict(X)[0])
    niveau, couleur, emoji, conseil = _get_alert(pm)
    return {
        'ville'     : obs.city,
        'region'    : obs.region,
        'date'      : obs.date,
        'pm25_proxy': round(pm, 2),
        'niveau'    : niveau,
        'couleur'   : couleur,
        'emoji'     : emoji,
        'conseil'   : conseil,
        'details'   : {
            'is_no_wind'      : int(d['is_no_wind']),
            'is_no_rain'      : int(d['is_no_rain']),
            'is_dry_season'   : int(d['is_dry_season']),
            'stagnation_score': int(d['stagnation_score']),
            'sunshine_ratio'  : round(float(d['sunshine_ratio']), 3),
        }
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["Info"])
def root():
    return {
        "message"  : "GENIUS — Air Quality Prediction API",
        "version"  : "1.0.0",
        "equipe"   : "GENIUS — IndabaX Cameroon 2026",
        "endpoints": ["/predict", "/predict/batch", "/cities", "/regions", "/health", "/docs"]
    }


@app.get("/health", tags=["Info"])
def health():
    return {
        "status"  : "ok",
        "model"   : "XGBoost PM2.5 Proxy",
        "metrics" : ARTIFACTS['model_metrics']
    }


@app.get("/cities", tags=["Référentiel"])
def get_cities():
    """Retourne la liste des 40 villes disponibles."""
    return {"cities": ARTIFACTS['le_city'].classes_.tolist(), "count": len(ARTIFACTS['le_city'].classes_)}


@app.get("/regions", tags=["Référentiel"])
def get_regions():
    """Retourne la liste des 10 régions disponibles."""
    return {"regions": ARTIFACTS['le_region'].classes_.tolist()}


@app.post("/predict", response_model=PredictionResponse, tags=["Prédiction"])
def predict(obs: MeteoInput):
    """
    Prédit le proxy PM2.5 et le niveau d'alerte pour une ville et une date données.
    """
    return _predict_one(obs)


@app.post("/predict/batch", tags=["Prédiction"])
def predict_batch(batch: BatchInput):
    """
    Prédiction par lot pour plusieurs villes/dates en une seule requête.
    """
    results = [_predict_one(obs) for obs in batch.observations]
    return {
        "count"  : len(results),
        "results": results,
        "summary": {
            "dangerous" : sum(1 for r in results if r['niveau'] == 'Dangereux'),
            "bad"       : sum(1 for r in results if r['niveau'] == 'Mauvais'),
            "moderate"  : sum(1 for r in results if r['niveau'] == 'Modéré'),
            "good"      : sum(1 for r in results if r['niveau'] == 'Bon'),
        }
    }
