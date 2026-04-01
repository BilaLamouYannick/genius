---
title: GENIUS Air Quality API
emoji: 🌍
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# GENIUS — API Qualité de l'Air · Cameroun

API FastAPI de prédiction du PM2.5 pour 40 villes camerounaises.

## Endpoints

- `GET /health` — statut de l'API
- `POST /predict` — prédiction PM2.5
- `GET /docs` — documentation interactive Swagger

## Exemple

```bash
curl -X POST https://BilaLamouYannick-genius-api.hf.space/predict \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Maroua",
    "region": "Extreme-Nord",
    "date": "2026-01-15",
    "temperature_2m_mean": 34.0,
    "temperature_2m_max": 40.0,
    "temperature_2m_min": 28.0,
    "precipitation_sum": 0.0,
    "wind_speed_10m_max": 3.5,
    "shortwave_radiation_sum": 22.0,
    "sunshine_duration": 35000.0,
    "et0_fao_evapotranspiration": 6.5,
    "latitude": 10.59,
    "longitude": 14.32
  }'
```
