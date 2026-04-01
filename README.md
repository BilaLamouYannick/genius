# 🌍 GENIUS — Prédiction de la Qualité de l'Air au Cameroun

**Hackathon IndabaX Cameroon 2026 · Équipe GENIUS**

> Système de prédiction du PM2.5 pour 40 villes camerounaises, basé sur XGBoost (R²=0.9999), avec API FastAPI et dashboard Streamlit interactif.

---

## Équipe

**Yannick SOKDOU BILA LAMOU · Félicia TCHAUGO · DOKI BABA G**

---

## Aperçu

GENIUS prédit la qualité de l'air (proxy PM2.5) à partir de données météorologiques journalières. Le système couvre les 10 régions du Cameroun et ses 40 principales villes, avec :

- 🗺️ **Carte de chaleur** interactive des 40 villes (niveaux de pollution en temps réel)
- 📅 **Prévision 30 jours** avec calendrier de risque coloré
- 📊 **Comparaison climat vs pollution** (double axe, corrélation)
- 🚦 **Indicateurs d'alerte** (Bon / Modéré / Mauvais / Dangereux)
- 🌍 **Analyse régionale** saisonnière

---

## Structure du projet

```
genius/
├── models/
│   ├── xgboost_pm25_genius.pkl     ← modèle XGBoost entraîné
│   └── model_metadata.json         ← métadonnées et formule proxy
|   └── GENIUS_Hackathon_IndabaX2026_COMPLET.ipynb  ← notebook complet
|
├── api/
│   └── main.py                     ← API FastAPI /predict
├── dashboard/
│   └── app.py                      ← Dashboard Streamlit
|
└── requirements.txt
```

---

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/BilaLamouYannick/genius.git
cd genius

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

---

## Lancer l'application

### Étape 1 — API FastAPI

```bash
cd api
uvicorn main:app --reload --port 8000
```

Documentation interactive : **http://localhost:8000/docs**

### Étape 2 — Dashboard Streamlit

```bash
cd dashboard
streamlit run app.py
```

Dashboard : **http://localhost:8501**

---

## Niveaux d'alerte PM2.5

| Emoji | Niveau    | Score PM2.5 | Conseil                                      |
|-------|-----------|-------------|----------------------------------------------|
| 🟢    | Bon       | < 16        | Activités sans restriction                   |
| 🟡    | Modéré    | 16 – 22     | Personnes sensibles : limiter les efforts    |
| 🟠    | Mauvais   | 22 – 28     | Éviter les activités physiques intenses      |
| 🔴    | Dangereux | > 28        | Rester à l'intérieur, masque recommandé      |

---

## Modèle

- **Algorithme** : XGBoost
- **Cible** : `pm25_proxy` (indicateur composite de pollution)
- **R²** : 0.9999
- **Variables clés** : température, rayonnement solaire, évapotranspiration, précipitations, vitesse du vent
- **Formule proxy** :
  ```
  pm25 = 0.35×T_moy + 0.25×SRAD + 0.20×ET0
       + 8×(vent<5km/h) + 5×(pluie=0) + 4×(saison_sèche)
  ```

---

## Exemple d'appel API

```bash
curl -X POST http://localhost:8000/predict \
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

---

*Projet réalisé dans le cadre du Hackathon IndabaX Cameroon 2026.*
