"""
GENIUS — Dashboard Qualité de l'Air · Cameroun
Hackathon IndabaX Cameroon 2026

Lancement :
  API       : cd api && uvicorn main:app --reload --port 8000
  Dashboard : cd dashboard && streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pickle, math, os, requests
from datetime import date, timedelta

# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="GENIUS · Air Quality", page_icon="🌿",
                   layout="wide", initial_sidebar_state="expanded")

# ── PWA : manifest + service worker ──────────────────────────
st.markdown("""
<link rel="manifest" href="/app/static/manifest.json">
<meta name="theme-color" content="#10B981">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="GENIUS">
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/app/static/sw.js')
        .then(r => console.log('GENIUS SW registered:', r.scope))
        .catch(e => console.log('GENIUS SW error:', e));
    });
  }
</script>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# STYLES
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, html, body { font-family: 'Inter', sans-serif !important; }
.block-container { padding: .8rem 1.4rem 2rem !important; max-width: 1500px; }

/* ── Cacher la barre Streamlit ── */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background:#0F172A !important; width:290px !important; min-width:290px !important; max-width:290px !important;
}
/* Bouton collapse natif Streamlit — stylisé */
[data-testid="collapsedControl"] {
    background: #1E293B !important;
    border-radius: 0 8px 8px 0 !important;
    border: 1px solid #334155 !important;
    border-left: none !important;
    top: 1rem !important;
}
[data-testid="collapsedControl"] button {
    color: #94A3B8 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: .6rem .9rem !important; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color:#94A3B8 !important; font-size:.75rem !important;
    font-weight:600 !important; margin-bottom:4px !important;
    padding-bottom:0 !important; line-height:1.3 !important; }
[data-testid="stSidebar"] .stSlider { padding-top:0 !important; padding-bottom:6px !important; margin-bottom:4px !important; }
[data-testid="stSidebar"] .stSlider > div { padding-top:0 !important; }
[data-testid="stSidebar"] .element-container { margin-bottom:4px !important; }
[data-testid="stSidebar"] p { color:#CBD5E1; font-size:.78rem; }
[data-testid="stSidebar"] hr { border-color:#1E293B !important; margin:.45rem 0 !important; }
/* Selectbox ville */
[data-testid="stSidebar"] .stSelectbox { margin-bottom:6px !important; }
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background:#1E293B !important; border-color:#475569 !important;
    color:#F1F5F9 !important; border-radius:8px !important; min-height:36px !important; font-size:.82rem !important;
}
[data-testid="stSidebar"] .stSelectbox svg { color:#94A3B8 !important; }
/* Date input */
[data-testid="stSidebar"] .stDateInput { margin-bottom:6px !important; }
[data-testid="stSidebar"] .stDateInput > div > div { background:#1E293B !important; border-color:#475569 !important; border-radius:8px !important; }
[data-testid="stSidebar"] .stDateInput input {
    background:#1E293B !important; border-color:#475569 !important;
    color:#F1F5F9 !important; border-radius:8px !important; padding:.3rem .6rem !important; font-size:.82rem !important;
}
[data-testid="stSidebar"] .stDateInput button { color:#94A3B8 !important; }

div[data-testid="stSidebar"] .stButton > button {
    width:100%; background:linear-gradient(135deg,#10B981,#059669) !important;
    color:white !important; font-weight:700 !important; font-size:.85rem !important;
    border:none !important; border-radius:9px !important; padding:.45rem !important;
    box-shadow:0 4px 12px rgba(16,185,129,.3) !important; margin-top:.2rem;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    transform:translateY(-1px) !important; box-shadow:0 6px 18px rgba(16,185,129,.4) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background:white; border-radius:10px; padding:.2rem;
    gap:.3rem; box-shadow:0 1px 4px rgba(0,0,0,.06); border:1px solid #E2E8F0;
}
.stTabs [data-baseweb="tab"] {
    border-radius:7px; font-weight:600; font-size:.82rem;
    padding:.3rem .85rem; color:#64748B !important;
}
.stTabs [aria-selected="true"] { background:#0F172A !important; color:white !important; }

/* ── Cards ── */
.kcard { background:white; border-radius:10px; padding:.65rem .85rem;
         box-shadow:0 1px 5px rgba(0,0,0,.05); border-left:4px solid var(--c); }
.kcard .v { font-size:1.55rem; font-weight:800; color:var(--c); line-height:1; }
.kcard .l { font-size:.65rem; color:#94A3B8; text-transform:uppercase;
            letter-spacing:.06em; margin-top:.15rem; }

/* ── Alert banner ── */
.alert-banner {
    border-radius:12px; padding:1rem 1.3rem;
    display:flex; align-items:center; gap:1.1rem;
    background:var(--bg); border-left:5px solid var(--c);
    box-shadow:0 2px 10px rgba(0,0,0,.06); margin-bottom:.6rem;
}
.alert-banner .score { font-size:2.4rem; font-weight:900; color:var(--c); line-height:1; }
.alert-banner .unit  { font-size:.78rem; color:#64748B; }
.alert-banner .level { font-size:1.05rem; font-weight:700; color:var(--c); }
.alert-banner .city  { font-size:.7rem; color:#94A3B8; text-transform:uppercase;
                       letter-spacing:.08em; margin-bottom:.2rem; }
.alert-banner .msg   { font-size:.82rem; color:#475569; margin-top:.25rem; max-width:360px; }

.sec { font-size:.88rem; font-weight:700; color:#0F172A;
       border-left:3px solid #10B981; padding-left:.55rem;
       margin:.9rem 0 .4rem; }

.pill { display:inline-flex; align-items:center; gap:.3rem;
        border-radius:20px; padding:.22rem .6rem; font-size:.73rem; font-weight:600;
        border:1px solid var(--c); color:var(--c); background:var(--bg); margin:.15rem; }

.footer { text-align:center; color:#94A3B8; font-size:.72rem;
          padding:.9rem 0 .4rem; border-top:1px solid #E2E8F0; margin-top:1.5rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# DONNÉES
# ──────────────────────────────────────────────────────────────
CITY_DATA = {
    "Maroua":      {"region":"Extreme-Nord","lat":10.59,"lon":14.32},
    "Kousseri":    {"region":"Extreme-Nord","lat":12.07,"lon":15.03},
    "Mokolo":      {"region":"Extreme-Nord","lat":10.74,"lon":13.80},
    "Yagoua":      {"region":"Extreme-Nord","lat":10.34,"lon":15.23},
    "Garoua":      {"region":"Nord",        "lat": 9.30,"lon":13.40},
    "Guider":      {"region":"Nord",        "lat": 9.93,"lon":13.94},
    "Poli":        {"region":"Nord",        "lat": 8.47,"lon":13.23},
    "Touboro":     {"region":"Nord",        "lat": 7.77,"lon":15.37},
    "Ngaoundere":  {"region":"Adamaoua",    "lat": 7.33,"lon":13.58},
    "Meiganga":    {"region":"Adamaoua",    "lat": 6.52,"lon":14.30},
    "Tibati":      {"region":"Adamaoua",    "lat": 6.47,"lon":12.62},
    "Tignere":     {"region":"Adamaoua",    "lat": 7.37,"lon":12.65},
    "Yaounde":     {"region":"Centre",      "lat": 3.87,"lon":11.52},
    "Bafia":       {"region":"Centre",      "lat": 4.75,"lon":11.23},
    "Akonolinga":  {"region":"Centre",      "lat": 3.77,"lon":12.25},
    "Mbalmayo":    {"region":"Centre",      "lat": 3.51,"lon":11.50},
    "Bertoua":     {"region":"Est",         "lat": 4.57,"lon":13.68},
    "Abong-Mbang": {"region":"Est",         "lat": 3.98,"lon":13.17},
    "Batouri":     {"region":"Est",         "lat": 4.43,"lon":14.36},
    "Yokadouma":   {"region":"Est",         "lat": 3.51,"lon":15.05},
    "Douala":      {"region":"Littoral",    "lat": 4.05,"lon": 9.70},
    "Edea":        {"region":"Littoral",    "lat": 3.80,"lon":10.13},
    "Nkongsamba":  {"region":"Littoral",    "lat": 4.95,"lon": 9.94},
    "Loum":        {"region":"Littoral",    "lat": 4.71,"lon": 9.73},
    "Bamenda":     {"region":"Nord-Ouest",  "lat": 5.96,"lon":10.15},
    "Kumbo":       {"region":"Nord-Ouest",  "lat": 6.20,"lon":10.67},
    "Wum":         {"region":"Nord-Ouest",  "lat": 6.03,"lon":10.07},
    "Mbengwi":     {"region":"Nord-Ouest",  "lat": 5.99,"lon":10.00},
    "Bafoussam":   {"region":"Ouest",       "lat": 5.48,"lon":10.42},
    "Dschang":     {"region":"Ouest",       "lat": 5.44,"lon":10.05},
    "Foumban":     {"region":"Ouest",       "lat": 5.72,"lon":10.90},
    "Mbouda":      {"region":"Ouest",       "lat": 5.62,"lon":10.25},
    "Ebolowa":     {"region":"Sud",         "lat": 2.91,"lon":11.15},
    "Kribi":       {"region":"Sud",         "lat": 2.95,"lon": 9.91},
    "Sangmelima":  {"region":"Sud",         "lat": 2.93,"lon":11.98},
    "Ambam":       {"region":"Sud",         "lat": 2.38,"lon":11.28},
    "Buea":        {"region":"Sud-Ouest",   "lat": 4.15,"lon": 9.24},
    "Limbe":       {"region":"Sud-Ouest",   "lat": 4.02,"lon": 9.20},
    "Kumba":       {"region":"Sud-Ouest",   "lat": 4.63,"lon": 9.44},
    "Mamfe":       {"region":"Sud-Ouest",   "lat": 5.75,"lon": 9.31},
}

# Valeurs climatiques typiques par région (moyennes dataset 2020-2025)
# Utilisées pour la prévision et la comparaison climat/qualité
REGION_CLIMATE = {
    "Extreme-Nord": {"tm_base":32,"rad_base":24,"et0_base":7.5,"rain_monthly":[0,0,0,5,20,40,80,90,60,20,2,0],"wind_base":6},
    "Nord":         {"tm_base":30,"rad_base":23,"et0_base":7.0,"rain_monthly":[0,0,2,10,35,70,120,110,80,25,3,0],"wind_base":7},
    "Adamaoua":     {"tm_base":25,"rad_base":20,"et0_base":5.5,"rain_monthly":[5,8,20,40,80,120,150,140,120,60,15,5],"wind_base":8},
    "Centre":       {"tm_base":24,"rad_base":17,"et0_base":4.5,"rain_monthly":[30,50,80,120,140,100,60,80,120,150,80,30],"wind_base":9},
    "Est":          {"tm_base":25,"rad_base":16,"et0_base":4.0,"rain_monthly":[20,40,70,110,130,100,60,70,110,140,70,20],"wind_base":8},
    "Littoral":     {"tm_base":26,"rad_base":16,"et0_base":4.2,"rain_monthly":[40,60,100,150,200,250,300,320,280,200,80,40],"wind_base":10},
    "Nord-Ouest":   {"tm_base":21,"rad_base":16,"et0_base":3.5,"rain_monthly":[10,20,50,100,150,200,250,280,220,120,30,10],"wind_base":9},
    "Ouest":        {"tm_base":22,"rad_base":17,"et0_base":3.8,"rain_monthly":[20,30,70,110,150,180,200,210,180,110,40,20],"wind_base":9},
    "Sud":          {"tm_base":25,"rad_base":15,"et0_base":4.0,"rain_monthly":[50,80,110,150,170,120,70,90,140,180,90,50],"wind_base":8},
    "Sud-Ouest":    {"tm_base":26,"rad_base":15,"et0_base":4.1,"rain_monthly":[40,60,120,180,250,350,420,450,380,260,100,50],"wind_base":10},
}

LEVELS = [
    ("Bon",       "#10B981","#D1FAE5","🟢"),
    ("Modéré",    "#F59E0B","#FEF3C7","🟡"),
    ("Mauvais",   "#F97316","#FFEDD5","🟠"),
    ("Dangereux", "#EF4444","#FEE2E2","🔴"),
]
LEVEL_MSGS = {
    "Bon":       "Qualité satisfaisante. Activités extérieures sans restriction.",
    "Modéré":    "Qualité acceptable. Personnes sensibles : limiter les efforts prolongés.",
    "Mauvais":   "Population sensible affectée. Éviter les activités physiques intenses.",
    "Dangereux": "Alerte critique ! Restez à l'intérieur. Consultation médicale recommandée.",
}

def get_level(pm):
    if pm < 16:   return LEVELS[0]
    elif pm < 22: return LEVELS[1]
    elif pm < 28: return LEVELS[2]
    else:         return LEVELS[3]

# ──────────────────────────────────────────────────────────────
# FORMULE PROXY — section 4.1 du notebook
# (équivalent XGBoost R²=0.9999)
# ──────────────────────────────────────────────────────────────
def proxy(tm, rad, et0, wnd, pr, month):
    no_wind = int(wnd < 5)
    no_rain = int(pr < 0.1)
    dry     = int(month in [11,12,1,2,3])
    return max(0.35*tm + 0.25*rad + 0.20*et0
               + 8.0*no_wind + 5.0*no_rain + 4.0*dry, 0.0)

# ──────────────────────────────────────────────────────────────
# CHARGEMENT MODÈLE + API
# ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_art():
    p = os.path.join(os.path.dirname(__file__), "..", "models", "xgboost_pm25_genius.pkl")
    with open(p, "rb") as f:
        return pickle.load(f)

try:
    ART = load_art()
except Exception as e:
    st.error(f"❌ Modèle introuvable : {e}"); st.stop()

API_URL = os.environ.get("API_URL", "http://localhost:8000")
def api_alive():
    try: return requests.get(f"{API_URL}/health", timeout=1.5).status_code == 200
    except: return False
API_OK = api_alive()

def predict_one(city, region, lat, lon, date_str, tm, wnd, pr, rad, et0):
    month = date.fromisoformat(date_str).month
    if API_OK:
        try:
            sun_sec = max((12 - pr/10) * 3600, 3600)
            r = requests.post(f"{API_URL}/predict", json={
                "city":city,"region":region,"date":date_str,
                "temperature_2m_mean":tm,"temperature_2m_max":tm+6,"temperature_2m_min":tm-6,
                "precipitation_sum":pr,"precipitation_hours":round(pr/2.5,1) if pr>0 else 0.0,
                "wind_speed_10m_max":wnd,"shortwave_radiation_sum":rad,
                "sunshine_duration":sun_sec,"et0_fao_evapotranspiration":et0,
                "daylight_duration":43200.0,"latitude":lat,"longitude":lon,
            }, timeout=5)
            r.raise_for_status()
            return float(r.json()["pm25_proxy"])
        except: pass
    return proxy(tm, rad, et0, wnd, pr, month)

# ──────────────────────────────────────────────────────────────
# GÉNÉRATION DES DONNÉES DE PRÉVISION
# ──────────────────────────────────────────────────────────────
def forecast_30days(city, region, lat, lon, start_date, tm, wnd, pr, rad, et0):
    """Génère une prévision sur 30 jours en faisant varier légèrement les conditions."""
    rows = []
    rng = np.random.default_rng(42)
    for i in range(30):
        d = start_date + timedelta(days=i)
        # Légère variation aléatoire réaliste
        tm_i  = tm  + rng.normal(0, 1.5)
        wnd_i = max(wnd + rng.normal(0, 2), 0)
        pr_i  = max(pr  + rng.normal(0, 3), 0)
        rad_i = max(rad + rng.normal(0, 2), 0)
        pm_i  = proxy(tm_i, rad_i, et0, wnd_i, pr_i, d.month)
        lv,col,bg,emj = get_level(pm_i)
        rows.append({"Date":d,"PM25":round(pm_i,2),"Niveau":lv,"Couleur":col,
                     "T":round(tm_i,1),"Vent":round(wnd_i,1),"Pluie":round(pr_i,1)})
    return pd.DataFrame(rows)

def monthly_climate_vs_pm(city, region, tm_base, wnd, pr_override, rad_base, et0_base):
    """Comparaison mensuelle climat vs PM2.5 pour une ville."""
    clim = REGION_CLIMATE.get(region, REGION_CLIMATE["Centre"])
    rows = []
    mois = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    for i, m in enumerate(range(1,13)):
        pr_m  = clim["rain_monthly"][i]
        wnd_m = clim["wind_base"] + (2 if m in [1,2,3,12] else -1)
        rad_m = rad_base + (3 if m in [11,12,1,2] else -2 if m in [6,7,8] else 0)
        et0_m = et0_base + (1.5 if m in [11,12,1,2,3] else -0.5)
        tm_m  = tm_base + (4 if m in [2,3,4] else -3 if m in [7,8] else 0)
        pm_m  = proxy(tm_m, rad_m, et0_m, wnd_m, pr_m, m)
        rows.append({"Mois":mois[i],"PM25":round(pm_m,2),
                     "T°":round(tm_m,1),"Pluie":round(pr_m,1),
                     "Vent":round(wnd_m,1),"SRAD":round(rad_m,1)})
    return pd.DataFrame(rows)

@st.cache_data(show_spinner=False)
def all_cities_snapshot(date_str, tm, wnd, pr, rad, et0):
    month = date.fromisoformat(date_str).month
    rows = []
    for city, info in CITY_DATA.items():
        # Légère variation géographique réaliste
        lat_factor = (info["lat"] - 5) * 0.3  # nord = plus chaud/sec
        tm_c  = tm  + lat_factor * 0.5
        wnd_c = max(wnd - lat_factor * 0.1, 0)
        pr_c  = max(pr  - lat_factor * 1.5, 0)
        pm = proxy(tm_c, rad, et0, wnd_c, pr_c, month)
        lv,col,bg,emj = get_level(pm)
        rows.append({"Ville":city,"Région":info["region"],
                     "Lat":info["lat"],"Lon":info["lon"],
                     "PM25":round(pm,2),"Niveau":lv,
                     "Couleur":col,"BG":bg,"Emoji":emj,
                     "Taille":round(max(pm,5)+3, 2)})
    return pd.DataFrame(rows)

# ──────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
# Pré-initialiser les widgets des onglets pour éviter le retour au tab 1
if "map_mode" not in st.session_state:
    st.session_state.map_mode = "🌡️ Heatmap densité"
if "clim_var" not in st.session_state:
    st.session_state.clim_var = "🌡️ Température"
if "scatter_var" not in st.session_state:
    st.session_state.scatter_var = "T°"
if "ca" not in st.session_state:
    st.session_state.ca = "Maroua"
if "cb" not in st.session_state:
    st.session_state.cb = "Douala"


# ──────────────────────────────────────────────────────────────
# SIDEBAR — COMPACTE, PAS DE SCROLL
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    # Header compact
    st.markdown("""
    <div style="text-align:center;padding:.15rem 0 .5rem">
      <div style="font-size:1.35rem;line-height:1">🌿</div>
      <div style="font-size:.95rem;font-weight:800;color:#F1F5F9;line-height:1.2">GENIUS</div>
      <div style="font-size:.62rem;color:#475569">Air Quality · Cameroun · 2026</div>
    </div>""", unsafe_allow_html=True)

    # Statut API
    dot, src = ("🟢", "API connectée") if API_OK else ("🔴", "Mode local")
    st.markdown(f"<div style='background:#1E293B;border-radius:5px;padding:.2rem .5rem;font-size:.65rem;color:#64748B;margin-bottom:.3rem;text-align:center'>{dot} {src} · R²={ART['model_metrics']['r2']:.4f}</div>", unsafe_allow_html=True)

    # Ville + Date — en colonne unique pour lisibilité
    cities_list = sorted(CITY_DATA.keys())
    city_sel = st.selectbox("🏙️ Ville", cities_list, index=cities_list.index("Maroua"))
    date_sel = st.date_input("📅 Date", value=date.today())

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 5 paramètres climatiques ──
    st.markdown("<div style='font-size:.67rem;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.2rem'>🌡️ Conditions climatiques</div>", unsafe_allow_html=True)

    temp_mean = st.slider("🌡️ T° moyenne (°C)",  -5.0, 50.0, 30.0, 0.5)
    precip    = st.slider("🌧️ Pluie (mm)",        0.0, 80.0,  0.0, 0.5)
    wind      = st.slider("💨 Vent max (km/h)",    0.0, 80.0,  5.0, 0.5)
    radiation = st.slider("☀️ SRAD (MJ/m²)",       0.0, 35.0, 22.0, 0.5)
    et0       = st.slider("💧 ET0 (mm)",           0.0, 12.0,  5.0, 0.1)

    # Alertes inline
    warns = []
    month_cur = date_sel.month
    if wind < 5:                   warns.append("💨 Vent faible")
    if precip < 0.1:               warns.append("🌵 Pas de pluie")
    if month_cur in [11,12,1,2,3]: warns.append("🌾 Saison sèche")
    if warns:
        st.markdown(f"<div style='background:#7F1D1D;border-radius:5px;padding:.2rem .5rem;font-size:.66rem;color:#FCA5A5;margin:.2rem 0;text-align:center'>"
                    + " · ".join(warns) + "</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    predict_btn = st.button("Prédire maintenant")

    # Légende
    st.markdown("""
    <div style='font-size:.63rem;color:#475569;line-height:1.75;margin-top:.2rem;text-align:center'>
    🟢 &lt;16 Bon · 🟡 16–22 Modéré<br>🟠 22–28 Mauvais · 🔴 &gt;28 Dangereux
    </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# CALCUL
# ──────────────────────────────────────────────────────────────
if predict_btn:
    ci   = CITY_DATA[city_sel]
    dstr = str(date_sel)
    with st.spinner("Calcul en cours…"):
        pm   = predict_one(city_sel, ci["region"], ci["lat"], ci["lon"],
                           dstr, temp_mean, wind, precip, radiation, et0)
        df_snap    = all_cities_snapshot(dstr, temp_mean, wind, precip, radiation, et0)
        df_fore    = forecast_30days(city_sel, ci["region"], ci["lat"], ci["lon"],
                                     date_sel, temp_mean, wind, precip, radiation, et0)
        df_clim_pm = monthly_climate_vs_pm(city_sel, ci["region"],
                                           REGION_CLIMATE.get(ci["region"],
                                           REGION_CLIMATE["Centre"])["tm_base"],
                                           wind, precip, radiation, et0)
    st.session_state.result = {
        "pm":pm,"city":city_sel,"region":ci["region"],"date":dstr,
        "month":month_cur,"tm":temp_mean,"wnd":wind,"pr":precip,
        "rad":radiation,"et0":et0,
        "df_snap":df_snap,"df_fore":df_fore,"df_clim":df_clim_pm,
        "no_wind":int(wind<5),"no_rain":int(precip<0.1),
        "is_dry":int(month_cur in [11,12,1,2,3]),
        "stag":min(int(wind<5)*3+int(precip<0.1)*2+int(month_cur in [11,12,1,2,3]),6),
    }

# ──────────────────────────────────────────────────────────────
# HEADER FIXE
# ──────────────────────────────────────────────────────────────
m_met = ART["model_metrics"]
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0F172A,#1E3A5F);border-radius:12px;
            padding:.75rem 1.3rem;margin-bottom:.7rem;box-shadow:0 4px 20px rgba(0,0,0,.18)">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem">
    <div style="display:flex;align-items:center;gap:.9rem">
      <div style="font-size:1.7rem;line-height:1">🌿</div>
      <div>
        <div style="font-size:1.15rem;font-weight:800;color:white;letter-spacing:-.01em;line-height:1.15">
          GENIUS <span style="color:#10B981">· Qualité de l'Air au Cameroun</span></div>
        <div style="display:flex;gap:.4rem;margin-top:.3rem;flex-wrap:wrap;align-items:center">
          <span style="background:rgba(16,185,129,.18);color:#10B981;border:1px solid rgba(16,185,129,.35);
                border-radius:20px;padding:.1rem .55rem;font-size:.66rem;font-weight:600"> IndabaX 2026</span>
          <span style="color:#64748B;font-size:.66rem">XGBoost R²={m_met['r2']:.4f} · MAE={m_met['mae']:.4f} · 40 villes · 10 régions</span>
        </div>
      </div>
    </div>
    <div style="font-size:.68rem;color:#475569;text-align:right;line-height:1.6">
      Yannick SOKDOU BILA LAMOU<br>Félicia TCHAUGO · DOKI BABA G
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# ÉTAT INITIAL
# ──────────────────────────────────────────────────────────────
if st.session_state.result is None:
    st.markdown("""
    <div style="text-align:center;padding:3.5rem 2rem;background:white;
                border-radius:16px;border:2px dashed #E2E8F0">
      
      <div style="font-size:1.2rem;font-weight:700;color:#1E293B;margin-top:.6rem">
        Configurez les paramètres et cliquez <em>Prédire maintenant</em>
      </div>
      <div style="font-size:.88rem;color:#94A3B8;margin-top:.4rem;max-width:480px;margin-inline:auto">
        Sélectionnez une ville, une date et les conditions climatiques dans le panneau gauche.<br>
        Le modèle génère instantanément une <strong>prédiction</strong>, une <strong>prévision 30 jours</strong>,
        une <strong>carte de chaleur</strong> et une <strong>comparaison climat/pollution</strong>.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ──────────────────────────────────────────────────────────────
# RÉSULTATS
# ──────────────────────────────────────────────────────────────
R     = st.session_state.result
pm    = R["pm"]
lv,col,bg,emj = get_level(pm)
msg   = LEVEL_MSGS[lv]
df_s  = R["df_snap"]
df_f  = R["df_fore"]
df_c  = R["df_clim"]

# ── KPI strip ──
n = {l[0]:(df_s["Niveau"]==l[0]).sum() for l in LEVELS}
cols_k = st.columns(5)
kpis = [
    ("🔴","Dangereux","#EF4444",n["Dangereux"],"villes"),
    ("🟠","Mauvais",  "#F97316",n["Mauvais"],  "villes"),
    ("🟡","Modéré",   "#F59E0B",n["Modéré"],   "villes"),
    ("🟢","Bon",      "#10B981",n["Bon"],       "villes"),
    ("📍",lv,          col,      f"{pm:.1f}",   "score sélection"),
]
for ci_k,(ic,lb,c,v,u) in zip(cols_k, kpis):
    ci_k.markdown(f'<div class="kcard" style="--c:{c}"><div class="v">{v}</div>'
                  f'<div class="l">{ic} {lb} — {u}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs — avec mémorisation de l'onglet actif ──
tab_labels = [
    "🎯 Alerte & Prévision",
    "🗺️ Carte de chaleur",
    "📊 Climat vs Pollution",
    "🏙️ Analyse régionale",
]
tab1, tab2, tab3, tab4 = st.tabs(tab_labels)

# ═══════════════════════════════════════════════
# TAB 1 — ALERTE + PRÉVISION 30 JOURS
# ═══════════════════════════════════════════════
with tab1:
    left, right = st.columns([1, 1.6], gap="large")

    with left:
        # Bannière alerte
        st.markdown(f"""
        <div class="alert-banner" style="--c:{col};--bg:{bg}">
          <div style="font-size:3.5rem;line-height:1">{emj}</div>
          <div style="flex:1">
            <div class="city">📍 {R['city']} · {R['region']} · {R['date']}</div>
            <div class="score">{pm:.1f}<span class="unit"> proxy PM2.5</span></div>
            <div class="level">{lv}</div>
            <div class="msg">{msg}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Facteurs actifs
        def pill_html(icon, label, active):
            c_ = "#EF4444" if active else "#10B981"
            b_ = "#FEF2F2" if active else "#F0FDF4"
            s  = "Actif ⚠️" if active else "OK ✓"
            return f'<span class="pill" style="--c:{c_};--bg:{b_}">{icon} {label} — {s}</span>'

        st.markdown(
            pill_html("💨","Stagnation",  R["no_wind"]) +
            pill_html("🌧️","Absence pluie",R["no_rain"]) +
            pill_html("🌾","Saison sèche", R["is_dry"]) +
            pill_html("🌡️","Chaleur >35°", int(R["tm"]>35)),
            unsafe_allow_html=True
        )

        # Score stagnation
        stag = R["stag"]
        pct  = stag / 6 * 100
        bar_col = "#EF4444" if stag>=4 else "#F97316" if stag>=2 else "#10B981"
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:.9rem 1.1rem;
                    margin-top:.7rem;box-shadow:0 1px 6px rgba(0,0,0,.06)">
          <div style="font-size:.72rem;color:#94A3B8;text-transform:uppercase;
                      letter-spacing:.06em;margin-bottom:.4rem">Score de stagnation atmosphérique</div>
          <div style="display:flex;align-items:center;gap:.8rem">
            <div style="flex:1;background:#F1F5F9;border-radius:4px;height:10px">
              <div style="width:{pct}%;background:{bar_col};height:10px;border-radius:4px;
                          transition:width .5s"></div>
            </div>
            <div style="font-size:1.4rem;font-weight:800;color:{bar_col};min-width:40px">{stag}/6</div>
          </div>
          <div style="font-size:.7rem;color:#64748B;margin-top:.3rem">
            Vent &lt;5 (+3) · Absence pluie (+2) · Saison sèche (+1 cap. à 6)
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Décomposition proxy
        st.markdown('<div class="sec">🧮 Décomposition du score</div>', unsafe_allow_html=True)
        contribs = {
            "🌡️ Température":   round(0.35*R["tm"],2),
            "☀️ Rayonnement":   round(0.25*R["rad"],2),
            "💧 ET0 (aridité)": round(0.20*R["et0"],2),
            "💨 Stagnation vent": 8*R["no_wind"],
            "🌧️ Absence pluie":  5*R["no_rain"],
            "🌾 Saison sèche":   4*R["is_dry"],
        }
        fig_c = go.Figure(go.Bar(
            x=list(contribs.values()), y=list(contribs.keys()),
            orientation="h",
            marker_color=["#6366F1","#8B5CF6","#A78BFA","#EF4444","#F97316","#F59E0B"],
            text=[f"{v:.1f}" for v in contribs.values()],
            textposition="outside",
        ))
        fig_c.update_layout(
            height=240, margin=dict(t=5,b=5,l=5,r=50),
            paper_bgcolor="white", plot_bgcolor="#F8FAFC",
            xaxis=dict(title="Contribution au score", gridcolor="#E2E8F0"),
            font=dict(family="Inter", size=11),
        )
        st.plotly_chart(fig_c, use_container_width=True)

    with right:
        # Prévision 30 jours
        st.markdown(f'<div class="sec">📅 Prévision 30 jours — {R["city"]}</div>', unsafe_allow_html=True)

        fig_fore = go.Figure()
        # Zone colorée par niveau
        for lv_n, c_n, bg_n, _ in LEVELS:
            mask = df_f["Niveau"] == lv_n
            if mask.any():
                dates_lv = df_f.loc[mask,"Date"].tolist()
                pm_lv    = df_f.loc[mask,"PM25"].tolist()
        # Bandes de fond
        for thresh_low, thresh_hi, c_n in [(0,16,"#D1FAE5"),(16,22,"#FEF3C7"),(22,28,"#FFEDD5"),(28,55,"#FEE2E2")]:
            fig_fore.add_hrect(y0=thresh_low, y1=thresh_hi,
                               fillcolor=c_n, opacity=0.35, line_width=0)
        # Ligne PM25
        fig_fore.add_trace(go.Scatter(
            x=df_f["Date"], y=df_f["PM25"],
            mode="lines+markers",
            line=dict(color=col, width=2.5),
            marker=dict(color=df_f["Couleur"], size=8, line=dict(color="white",width=1.5)),
            name="Score PM2.5",
            hovertemplate="<b>%{x|%d %b}</b><br>PM2.5: %{y:.1f}<extra></extra>",
        ))
        # Seuils
        for thresh, label, c_l in [(16,"Bon","#10B981"),(22,"Modéré","#F59E0B"),(28,"Mauvais","#F97316")]:
            fig_fore.add_hline(y=thresh, line_dash="dot", line_color=c_l, line_width=1.5,
                               annotation_text=label, annotation_font_size=10,
                               annotation_font_color=c_l)
        fig_fore.update_layout(
            height=320,
            xaxis=dict(title="", tickformat="%d %b", gridcolor="#E2E8F0"),
            yaxis=dict(title="Score proxy PM2.5", range=[0,50], gridcolor="#E2E8F0"),
            paper_bgcolor="white", plot_bgcolor="white",
            font=dict(family="Inter"), showlegend=False,
            margin=dict(t=10,b=30,l=10,r=10),
        )
        st.plotly_chart(fig_fore, use_container_width=True)

        # Statistiques de prévision
        fc1, fc2, fc3, fc4 = st.columns(4)
        for col_fc, label, val in [
            (fc1, "Moy. 30j",   f"{df_f['PM25'].mean():.1f}"),
            (fc2, "Max",        f"{df_f['PM25'].max():.1f}"),
            (fc3, "Min",        f"{df_f['PM25'].min():.1f}"),
            (fc4, "Jours alerte", f"{(df_f['Niveau'].isin(['Mauvais','Dangereux'])).sum()}"),
        ]:
            col_fc.metric(label, val)

        # Calendrier de risque — heatmap grille 7×5
        st.markdown('<div class="sec">🗓️ Calendrier de risque 30 jours</div>', unsafe_allow_html=True)

        JOURS_NOM = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]
        # Décalage : quel jour de semaine commence la prévision ?
        start_dow = df_f["Date"].iloc[0].weekday()  # 0=Lun

        # Grille 5 lignes × 7 colonnes = 35 cases, on ne remplit que les 30 jours
        n_rows = 5
        pm_grid    = [[None]*7 for _ in range(n_rows)]
        label_grid = [[""] *7 for _ in range(n_rows)]
        hover_grid = [[""] *7 for _ in range(n_rows)]

        for i, row in df_f.iterrows():
            pos = i + start_dow          # position linéaire dans la grille
            r, c = divmod(pos, 7)
            if r < n_rows:
                pm_grid[r][c]    = row["PM25"]
                label_grid[r][c] = row["Date"].strftime("%d")
                hover_grid[r][c] = f"{row['Date'].strftime('%a %d %b')}<br>PM2.5 : {row['PM25']:.1f}<br>{row['Niveau']}"

        fig_cal = go.Figure(go.Heatmap(
            z=pm_grid,
            text=label_grid,
            customdata=hover_grid,
            texttemplate="%{text}",
            textfont=dict(size=11, family="Inter"),
            colorscale=[
                [0.00, "#D1FAE5"],
                [0.35, "#FEF3C7"],
                [0.60, "#FFEDD5"],
                [1.00, "#FEE2E2"],
            ],
            zmin=8, zmax=42,
            xgap=3, ygap=3,
            hovertemplate="%{customdata}<extra></extra>",
            colorbar=dict(
                title="PM2.5", thickness=10, len=0.9,
                tickvals=[10,16,22,28,38],
                ticktext=["10","Bon 16","Mod. 22","Mauv. 28","38"],
                tickfont=dict(size=8),
            ),
        ))
        fig_cal.update_layout(
            height=220,
            margin=dict(t=4, b=4, l=4, r=60),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(
                tickvals=list(range(7)), ticktext=JOURS_NOM,
                tickfont=dict(size=9, color="#64748B"),
                side="top", showgrid=False, zeroline=False,
            ),
            yaxis=dict(visible=False, autorange="reversed"),
        )
        st.plotly_chart(fig_cal, use_container_width=True)

# ═══════════════════════════════════════════════
# TAB 2 — CARTE DE CHALEUR
# ═══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="sec">🗺️ Carte de chaleur PM2.5 — 40 villes du Cameroun</div>', unsafe_allow_html=True)

    map_mode = st.radio("Mode carte", ["🌡️ Heatmap densité", "🔵 Bulles d'alerte"],
                        horizontal=True, label_visibility="collapsed", key="map_mode")

    if "Heatmap" in map_mode:
        fig_map = go.Figure(go.Densitymapbox(
            lat=df_s["Lat"], lon=df_s["Lon"],
            z=df_s["PM25"],
            radius=60, opacity=0.7,
            colorscale=[
                [0.0,  "#10B981"], [0.35, "#F59E0B"],
                [0.6,  "#F97316"], [1.0,  "#EF4444"],
            ],
            zmin=8, zmax=42,
            colorbar=dict(title="PM2.5", tickfont_size=11),
            hovertemplate="<b>%{customdata}</b><br>PM2.5: %{z:.1f}<extra></extra>",
            customdata=df_s["Ville"],
        ))
    else:
        fig_map = px.scatter_mapbox(
            df_s, lat="Lat", lon="Lon",
            color="Niveau",
            color_discrete_map={l[0]:l[1] for l in LEVELS},
            size="Taille", size_max=35,
            hover_name="Ville",
            hover_data={"Région":True,"PM25":True,"Niveau":True,
                        "Taille":False,"Lat":False,"Lon":False},
        )

    fig_map.update_layout(
        mapbox=dict(style="carto-positron", zoom=5,
                    center={"lat":5.5,"lon":12.5}),
        margin=dict(r=0,l=0,t=0,b=0),
        height=520, paper_bgcolor="white",
        legend=dict(title="Niveau", bgcolor="rgba(255,255,255,.92)",
                    bordercolor="#E2E8F0", borderwidth=1),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Top 10 + donut côte à côte
    c_top, c_pie = st.columns([1.5, 1], gap="large")
    with c_top:
        st.markdown('<div class="sec">🏙️ Top 10 villes les plus polluées</div>', unsafe_allow_html=True)
        top10 = df_s.nlargest(10,"PM25")[["Emoji","Ville","Région","PM25","Niveau"]].reset_index(drop=True)
        top10.columns = ["","Ville","Région","Score PM2.5","Niveau"]
        def hl(row):
            c_ = {l[0]:l[1] for l in LEVELS}.get(row["Niveau"],"#fff")
            return [f"background:{c_}18;border-left:3px solid {c_}"]+[""]*4
        st.dataframe(top10.style.apply(hl,axis=1).format({"Score PM2.5":"{:.2f}"}),
                     use_container_width=True, hide_index=True, height=320)

    with c_pie:
        st.markdown('<div class="sec">📊 Répartition nationale</div>', unsafe_allow_html=True)
        pie_df = df_s["Niveau"].value_counts().reset_index()
        pie_df.columns = ["Niveau","Nb"]
        fig_p = px.pie(pie_df, names="Niveau", values="Nb",
                       color="Niveau", color_discrete_map={l[0]:l[1] for l in LEVELS},
                       hole=0.55, height=220)
        fig_p.update_traces(textinfo="percent+label", textfont_size=11,
                            marker=dict(line=dict(color="white",width=2)))
        fig_p.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0),
                            paper_bgcolor="white")
        st.plotly_chart(fig_p, use_container_width=True)

# ═══════════════════════════════════════════════
# TAB 3 — COMPARAISON CLIMAT vs POLLUTION
# ═══════════════════════════════════════════════
with tab3:
    st.markdown(f'<div class="sec">📊 Comparaison climat vs qualité de l\'air — {R["city"]}</div>', unsafe_allow_html=True)

    st.caption("Variation mensuelle basée sur les moyennes climatiques typiques de la région sur 2020-2025")

    # Graphe dual-axis : PM2.5 + variable climatique choisie
    clim_var = st.radio("Variable climatique à comparer",
                        ["🌡️ Température","🌧️ Précipitations","💨 Vent","☀️ Rayonnement"],
                        horizontal=True, label_visibility="collapsed", key="clim_var")

    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
    mois_labels = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]

    # Barres PM2.5 colorées
    colors_m = [get_level(p)[1] for p in df_c["PM25"]]
    fig_dual.add_trace(go.Bar(
        x=mois_labels, y=df_c["PM25"],
        name="Score PM2.5",
        marker_color=colors_m,
        text=df_c["PM25"].apply(lambda x:f"{x:.1f}"),
        textposition="outside", textfont_size=9,
    ), secondary_y=False)

    # Ligne variable climatique
    var_map = {"🌡️ Température":("T°","°C","#6366F1"),
               "🌧️ Précipitations":("Pluie","mm","#3B82F6"),
               "💨 Vent":("Vent","km/h","#06B6D4"),
               "☀️ Rayonnement":("SRAD","MJ/m²","#F59E0B")}
    col_k, unit_k, col_line = var_map[clim_var]
    fig_dual.add_trace(go.Scatter(
        x=mois_labels, y=df_c[col_k],
        name=f"{clim_var} ({unit_k})",
        mode="lines+markers",
        line=dict(color=col_line, width=2.5, dash="dot"),
        marker=dict(size=7, color=col_line),
    ), secondary_y=True)

    for thresh, c_t in [(16,"#10B981"),(22,"#F59E0B"),(28,"#F97316")]:
        fig_dual.add_hline(y=thresh, line_dash="dot", line_color=c_t, line_width=1, secondary_y=False)

    fig_dual.update_layout(
        height=380, paper_bgcolor="white", plot_bgcolor="#F8FAFC",
        font=dict(family="Inter"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30,b=30,l=10,r=10),
        yaxis=dict(title="Score proxy PM2.5", range=[0,50], gridcolor="#E2E8F0"),
        yaxis2=dict(title=f"{clim_var} ({unit_k})", gridcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_dual, use_container_width=True)

    # Matrice de corrélation visuelle
    st.markdown('<div class="sec">🔗 Impact des facteurs climatiques sur la pollution</div>', unsafe_allow_html=True)
    corr_data = {
        "Facteur": ["T° moy","Rayonnement","ET0","Vent (< 5)","Pluie (absente)","Saison sèche"],
        "Coefficient": [0.35, 0.25, 0.20, 8.0, 5.0, 4.0],
        "Direction": ["+","+","+","+ (stagnation)","+ (absence)","+ (saisonnier)"],
        "Interprétation": [
            "Chaleur → photolyse → formation PM2.5",
            "Radiation → photochimie atmosphérique",
            "Aridité → resuspension particules",
            "Stagnation → accumulation pollution",
            "Absence lessivage humide",
            "Harmattan, feux de brousse",
        ]
    }
    st.dataframe(pd.DataFrame(corr_data), use_container_width=True, hide_index=True)

    # Scatter plot : un facteur vs PM2.5 mensuel
    st.markdown('<div class="sec">📈 Relation mensuelle (toutes régions)</div>', unsafe_allow_html=True)
    scatter_var = st.selectbox("Variable X", ["T°","Pluie","Vent","SRAD"], label_visibility="collapsed", key="scatter_var")
    fig_sc = px.scatter(df_c, x=scatter_var, y="PM25", text="Mois",
                        color="PM25",
                        color_continuous_scale=["#10B981","#F59E0B","#F97316","#EF4444"],
                        range_color=[8,42], height=320,
                        labels={scatter_var: f"{scatter_var}", "PM25": "Score PM2.5"})
    fig_sc.update_traces(textposition="top center", textfont_size=10,
                         marker=dict(size=14, line=dict(color="white",width=1.5)))
    fig_sc.update_layout(paper_bgcolor="white", plot_bgcolor="#F8FAFC",
                         font=dict(family="Inter"), margin=dict(t=10,b=30))
    st.plotly_chart(fig_sc, use_container_width=True)

# ═══════════════════════════════════════════════
# TAB 4 — ANALYSE RÉGIONALE
# ═══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="sec">📊 Score PM2.5 moyen par région</div>', unsafe_allow_html=True)

    df_reg = (df_s.groupby("Région")["PM25"]
              .agg(["mean","min","max","count"]).reset_index()
              .rename(columns={"mean":"Moy","min":"Min","max":"Max","count":"Villes"})
              .sort_values("Moy", ascending=False))
    df_reg["Couleur"] = df_reg["Moy"].apply(lambda x: get_level(x)[1])

    fig_reg = go.Figure()
    fig_reg.add_trace(go.Bar(
        x=df_reg["Région"], y=df_reg["Moy"],
        marker_color=df_reg["Couleur"],
        text=df_reg["Moy"].apply(lambda x:f"{x:.1f}"),
        textposition="outside",
        error_y=dict(type="data", symmetric=False,
                     array=(df_reg["Max"]-df_reg["Moy"]).tolist(),
                     arrayminus=(df_reg["Moy"]-df_reg["Min"]).tolist(),
                     color="#94A3B8", thickness=1.5, width=6),
    ))
    for thresh, lbl, c_t in [(16,"Bon","#10B981"),(22,"Modéré","#F59E0B"),(28,"Mauvais","#F97316")]:
        fig_reg.add_hline(y=thresh, line_dash="dot", line_color=c_t, line_width=1.5,
                          annotation_text=lbl, annotation_font_color=c_t, annotation_font_size=10)
    fig_reg.update_layout(
        height=380, paper_bgcolor="white", plot_bgcolor="#F8FAFC",
        yaxis=dict(title="Score proxy PM2.5", range=[0,50], gridcolor="#E2E8F0"),
        font=dict(family="Inter"), margin=dict(t=30,b=40),
    )
    st.plotly_chart(fig_reg, use_container_width=True)

    # Comparaison 2 villes sur l'année
    st.markdown('<div class="sec">🔀 Comparaison saisonnière inter-villes</div>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1: city_a = st.selectbox("Ville A", cities_list, index=cities_list.index(R["city"]), key="ca")
    with cc2: city_b = st.selectbox("Ville B", cities_list, index=cities_list.index("Douala"), key="cb")

    mois_l = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    clim_a = REGION_CLIMATE.get(CITY_DATA[city_a]["region"], REGION_CLIMATE["Centre"])
    clim_b = REGION_CLIMATE.get(CITY_DATA[city_b]["region"], REGION_CLIMATE["Centre"])

    def city_annual(clim):
        return [proxy(
            clim["tm_base"] + (4 if m in [2,3,4] else -3 if m in [7,8] else 0),
            clim["rad_base"] + (3 if m in [11,12,1,2] else -2 if m in [6,7,8] else 0),
            clim["et0_base"] + (1.5 if m in [11,12,1,2,3] else -0.5),
            max(clim["wind_base"] + (2 if m in [1,2,3,12] else -1), 0),
            clim["rain_monthly"][m-1], m
        ) for m in range(1,13)]

    pm_a_ann = city_annual(clim_a)
    pm_b_ann = city_annual(clim_b)

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Scatter(
        x=mois_l, y=pm_a_ann, name=city_a, mode="lines+markers",
        line=dict(color="#6366F1",width=2.5), marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(99,102,241,.08)",
    ))
    fig_cmp.add_trace(go.Scatter(
        x=mois_l, y=pm_b_ann, name=city_b, mode="lines+markers",
        line=dict(color="#EF4444",width=2.5), marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(239,68,68,.08)",
    ))
    for thresh, c_t in [(16,"#10B981"),(22,"#F59E0B"),(28,"#F97316")]:
        fig_cmp.add_hline(y=thresh, line_dash="dot", line_color=c_t, line_width=1)
    fig_cmp.update_layout(
        height=360, paper_bgcolor="white", plot_bgcolor="#F8FAFC",
        font=dict(family="Inter"),
        yaxis=dict(title="Score proxy PM2.5", range=[0,50], gridcolor="#E2E8F0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=20,b=30),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

# ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  🏆 Équipe <strong>GENIUS</strong> · IndabaX Cameroon 2026
  &nbsp;·&nbsp; Yannick SOKDOU · Félicia TCHAUGO · DOKI BABA G<br>
  XGBoost R²=0.9999 · Proxy PM2.5 · 40 villes · 10 régions
</div>
""", unsafe_allow_html=True)
