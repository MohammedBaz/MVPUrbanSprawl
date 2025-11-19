# app.py - ULTIMATE PROFESSIONAL VERSION (v2.1)
# Features: Fixed Map Scaling + Re-integrated GIF + Methodologies
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import math
import folium
from streamlit_folium import st_folium
from io import BytesIO

# ---------- Configuration ----------
st.set_page_config(page_title="SDG 11.3.1 Analytics Platform", layout="wide", page_icon="🏙️")

# City Coordinates (Lat, Lon)
CITY_COORDS = {
    "Riyadh": [24.7136, 46.6753],
    "Jeddah": [21.2854, 39.2376]
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
        raise RuntimeError(f"Failed to load CSV: {e}")
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

def calculate_radius(area_km2):
    """Convert Area (km2) to Radius (meters)."""
    if area_km2 <= 0: return 0
    # Area = pi * r^2  => r = sqrt(Area / pi)
    radius_km = math.sqrt(area_km2 / math.pi)
    return radius_km * 1000  # convert to meters

# ---------- Load Data ----------
DATA_URL = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/saudi_cities_sdg1131_1975_2025.csv?raw=1"

try:
    df_all = load_csv_from_github(DATA_URL)
except Exception:
    st.error("System Error: Unable to connect to the Data Repository.")
    st.stop()

# ---------- Sidebar Controls ----------
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
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", 
    "🗺️ Geospatial Analysis", 
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
    # Historical Chart
    years = [1975, 1990, 2000, 2015, 2020, 2025]
    vals = [row.get(f"Built-up {y} (km²)") for y in years]
    df_hist = pd.DataFrame({"Year": years, "Built-up (km²)": vals}).dropna()
    
    fig = px.area(df_hist, x="Year", y="Built-up (km²)", title=f"{city}: Urban Expansion Timeline")
    fig.update_traces(line_color='#2980b9')
    fig.update_layout(yaxis=dict(rangemode="tozero")) 
    st.plotly_chart(fig, use_container_width=True)

# === TAB 2: GEOSPATIAL ANALYSIS (Map + GIF) ===
with tab2:
    st.markdown("### Satellite-Derived Urban Extent")
    
    # Layout: Left = Interactive Context Map, Right = Detailed Time-Lapse GIF
    col_map, col_gif = st.columns([1, 1])
    
    with col_map:
        st.markdown("#### 📍 Location Context")
        st.caption("Visualizing total area scale (Circle = Estimated Area)")
        
        # Map
        m = folium.Map(location=CITY_COORDS[city], zoom_start=10, tiles="CartoDB positron")
        
        # Visualizing 2025 Area
        r_2025 = calculate_radius(row['Built-up 2025 (km²)'])
        folium.Circle(
            location=CITY_COORDS[city],
            radius=r_2025,
            color="#e74c3c",
            weight=2,
            fill=True,
            fill_opacity=0.2,
            tooltip=f"Estimated Urban Zone 2025"
        ).add_to(m)
        
        st_folium(m, height=400, use_container_width=True)
    
    with col_gif:
        st.markdown("#### 🛰️ Detailed Evolution (Time-Lapse)")
        st.caption("Granular changes detected via Satellite Imagery (1985-2023)")
        
        # Load GIF
        gif_file = "Riyadh_expansion.gif" if city == "Riyadh" else "Jeddah_expansion.gif"
        gif_url = f"https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/{gif_file}?raw=1"
        gif_bytes = safe_image_from_url(gif_url)
        
        if gif_bytes:
            st.image(gif_bytes, use_column_width=True)
        else:
            st.warning("Satellite animation loading...")
            # Fallback
            st.image(f"https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/{city}_expansion_static.png?raw=1")

    st.info("ℹ️ **Technical Note:** The map on the left represents the *statistical extent* (Total Area). The animation on the right represents the *vector reality* (Actual Shapes).")

# === TAB 3: SIMULATION ===
with tab3:
    st.subheader(f"Scenario: {city} in 2030")
    st.write("Based on the parameters selected in the Sidebar.")
    
    current_pop = row["Population 2025"]
    current_built = row["Built-up 2025 (km²)"]
    years_forecast = 5 
    
    future_pop = current_pop * ((1 + sim_pop_growth/100) ** years_forecast)
    future_built = current_built * ((1 + sim_land_consumption/100) ** years_forecast)
    sim_ratio = sim_land_consumption / sim_pop_growth if sim_pop_growth != 0 else 0
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Projected Pop (2030)", format_num
