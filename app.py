# app.py - ULTIMATE PROFESSIONAL VERSION (v5.0 - Accurate Boundaries)
# Features: Real City Shapes (Hardcoded), Simulation, Methodology
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import folium
from streamlit_folium import st_folium

# ---------- Configuration ----------
st.set_page_config(page_title="SDG 11.3.1 Analytics Platform", layout="wide", page_icon="🏙️")

# ---------- ACCURATE GEOSPATIAL DATA (Hardcoded for Stability) ----------
# These coordinates represent the simplified urban extent of the cities.
# No external GeoJSON file is required.

CITY_POLYGONS = {
    "Riyadh": {
        "type": "Feature",
        "properties": {"name": "Riyadh Urban Extent"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [46.550, 24.920], [46.720, 24.950], [46.850, 24.900], # North (Airport)
                [46.950, 24.800], [46.980, 24.650],                   # East
                [46.900, 24.500], [46.750, 24.400],                   # South
                [46.600, 24.450], [46.520, 24.550], [46.480, 24.700], # West (Wadi Hanifa)
                [46.550, 24.920]                                      # Closing Loop
            ]]
        }
    },
    "Jeddah": {
        "type": "Feature",
        "properties": {"name": "Jeddah Urban Extent"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [39.080, 21.850], [39.150, 21.850], # North (Obhur)
                [39.220, 21.700], [39.280, 21.550], [39.320, 21.400], # East (Mountains)
                [39.250, 21.200], [39.150, 21.150],                   # South
                [39.100, 21.250], [39.050, 21.450], [39.070, 21.650], # West (Coast)
                [39.080, 21.850]                                      # Closing Loop
            ]]
        }
    }
}

# Center points for the map
CITY_CENTERS = {
    "Riyadh": [24.7136, 46.6753],
    "Jeddah": [21.5000, 39.1700]
}

# ---------- Helpers ----------
def github_raw(url: str) -> str:
    if "?raw=1" in url: return url
    if "raw.githubusercontent.com" in url: return url + "?raw=1"
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/") + "?raw=1"
    return url

@st.cache_data(ttl=3600)
def load_csv_from_github(url: str) -> pd.DataFrame:
    url = github_raw(url)
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Failed to load CSV: {e}")
        st.stop()
    return df

def safe_image_from_url(url: str):
    url = github_raw(url)
    try:
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        return None
    return None

def format_num(n):
    return f"{n:,.0f}"

# ---------- Load Data ----------
# Main Statistical Data
DATA_URL = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/saudi_cities_sdg1131_1975_2025.csv?raw=1"
df_all = load_csv_from_github(DATA_URL)

# ---------- Sidebar Controls ----------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Saudi_Vision_2030_logo.svg/1200px-Saudi_Vision_2030_logo.svg.png", width=150)
st.sidebar.title("Control Panel")

# 1. City Selection
city = st.sidebar.selectbox("Select Urban Area", ["Riyadh", "Jeddah"], index=0)

# Filter Data
df = df_all[df_all["City"] == city].reset_index(drop=True)
if df.empty: st.stop()
row = df.iloc[0]

# 2. Simulation Parameters
st.sidebar.markdown("---")
st.sidebar.header("🔮 2030 Scenario Simulator")
st.sidebar.info("Adjust parameters to model future urban expansion.")
sim_pop_growth = st.sidebar.slider("Annual Pop. Growth (%)", 0.5, 5.0, 2.5, 0.1)
sim_land_consumption = st.sidebar.slider("Annual Land Consumption (%)", 0.5, 5.0, 3.2, 0.1)

# ---------- Header ----------
st.markdown(
    f"<h1 style='text-align: center; color: #16a085;'>SDG 11.3.1 Monitor: {city}</h1>", 
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center;'>Monitoring Land Consumption vs. Population Growth using Satellite Intelligence</p>", 
    unsafe_allow_html=True
)

# ---------- Main Tabs ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "🗺️ Geospatial Analysis", 
    "📈 Historical Trends", 
    "🔮 Prediction Model", 
    "📝 Methodology"
])

# === TAB 1: DASHBOARD ===
with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Built-up Area (2025)", f"{format_num(row['Built-up 2025 (km²)'])} km²")
    c2.metric("Population (2025)", f"{format_num(row['Population 2025'])}")
    sdg_val = row['SDG 11.3.1 Ratio (2020-25)']
    c3.metric("Current SDG 11.3.1 Ratio", f"{sdg_val:.3f}", 
              delta="Efficient" if sdg_val <= 1 else "Sprawling", delta_color="inverse")
    
    st.markdown("---")
    st.subheader("📦 Geospatial Database Export")
    st.write("Download the processed urban indicators for integration with GIS systems.")
    
    csv = df_all.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Full Dataset (CSV)",
        csv,
        "saudi_sdg1131_data.csv",
        "text/csv",
        key='download-csv'
    )

# === TAB 2: GEOSPATIAL ANALYSIS (Combined Map + GIF) ===
with tab2:
    st.markdown("### Satellite-Derived Urban Extent")
    
    col_
