# app.py - ULTIMATE PROFESSIONAL VERSION (v3.0)
# Features: GeoJSON Polygons (Accuracy), Population Modeling, Methodology
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import folium
import json
from streamlit_folium import st_folium

# ---------- Configuration ----------
st.set_page_config(page_title="SDG 11.3.1 Analytics Platform", layout="wide", page_icon="🏙️")

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

@st.cache_data(ttl=3600)
def load_geojson_from_github(url: str):
    """Load GeoJSON from GitHub or Local for the map."""
    url = github_raw(url)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None

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
# 1. CSV Data
CSV_URL = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/saudi_cities_sdg1131_1975_2025.csv?raw=1"
df_all = load_csv_from_github(CSV_URL)

# 2. GeoJSON Data (The new accurate file)
# NOTE: Ensure 'regions.geojson' is uploaded to your GitHub repo!
GEOJSON_URL = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/regions.geojson?raw=1"
geo_data = load_geojson_from_github(GEOJSON_URL)

# ---------- Sidebar Controls ----------
st.sidebar.title("Control Panel")

city = st.sidebar.selectbox("Select Urban Area", ["Riyadh", "Jeddah"], index=0)

# Filter Data
df = df_all[df_all["City"] == city].reset_index(drop=True)
if df.empty: st.stop()
row = df.iloc[0]

# Simulation Controls
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
    years = [1975, 1990, 2000, 2015, 2020, 2025]
    vals = [row.get(f"Built-up {y} (km²)") for y in years]
    df_hist = pd.DataFrame({"Year": years, "Built-up (km²)": vals}).dropna()
    fig = px.area(df_hist, x="Year", y="Built-up (km²)", title=f"{city}: Urban Expansion Timeline")
    fig.update_traces(line_color='#2980b9')
    fig.update_layout(yaxis=dict(rangemode="tozero")) 
    st.plotly_chart(fig, use_container_width=True)

# === TAB 2: GEOSPATIAL ANALYSIS (UPDATED WITH GEOJSON) ===
with tab2:
    st.markdown("### Satellite-Derived Urban Extent")
    
    col_map, col_gif = st.columns([1, 1])
    
    with col_map:
        st.markdown("#### 📍 Regional Boundaries (Vector)")
        st.caption("Accurate administrative/regional boundaries from Geospatial Database.")
        
        # Default center if GeoJSON fails
        default_locs = {"Riyadh": [24.7136, 46.6753], "Jeddah": [21.2854, 39.2376]}
        map_center = default_locs.get(city, [24, 46])
        
        # Initialize Map
        m = folium.Map(location=map_center, zoom_start=9, tiles="CartoDB positron")
        
        # Filter and Add GeoJSON
        found_feature = False
        if geo_data:
            # Try to find the feature matching the selected city
            # Logic: Look for 'name', 'Name', 'NAME_EN' in properties
            selected_feature = None
            for feature in geo_data.get('features', []):
                props = feature.get('properties', {})
                # Check common keys for the city name
                name_vals = [str(v).lower() for v in props.values()]
                if city.lower() in name_vals:
                    selected_feature = feature
                    break
            
            if selected_feature:
                found_feature = True
                # Add the polygon
                folium.GeoJson(
                    selected_feature,
                    name="Urban Boundary",
                    style_function=lambda x: {
                        'fillColor': '#e74c3c',
                        'color': '#c0392b',
                        'weight': 2,
                        'fillOpacity': 0.3
                    },
                    tooltip=f"{city} Region Boundary"
                ).add_to(m)
                
                # Optional: Center map on the polygon centroid if geometry is simple
                try:
                    # Rough centroid calculation for better zoom
                    coords = selected_feature['geometry']['coordinates'][0]
                    # Handle MultiPolygon vs Polygon logic if necessary
                    # Simple average of first ring
                    if len(coords) > 0:
                        # Flatten if needed (MultiPolygon structure varies)
                        while isinstance(coords[0][0], list): 
                             coords = coords[0]
                        lats = [p[1] for p in coords]
                        lons = [p[0] for p in coords]
                        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
                except:
                    pass # Fallback to default zoom
            else:
                st.warning(f"Boundaries for {city} not found in regions.geojson")
        
        if not found_feature:
            # Fallback to circle if GeoJSON fails or city not found
            folium.Circle(location=map_center, radius=20000, color="red").add_to(m)

        st_folium(m, height=400, use_container_width=True)
    
    with col_gif:
        st.markdown("#### 🛰️ Detailed Evolution (Time-Lapse)")
        st.caption("Granular changes detected via Satellite Imagery (1985-2023)")
        
        gif_file = "Riyadh_expansion.gif" if city == "Riyadh" else "Jeddah_expansion.gif"
        gif_url = f"https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/{gif_file}?raw=1"
        gif_bytes = safe_image_from_url(gif_url)
        
        if gif_bytes:
            st.image(gif_bytes, use_column_width=True)
        else:
            st.image(f"https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/{city}_expansion_static.png?raw=1")

# === TAB 3: SIMULATION ===
with tab3:
    st.subheader(f"Scenario: {city} in 2030")
    current_pop = row["Population 2025"]
    current_built = row["Built-up 2025 (km²)"]
    years_forecast = 5 
    future_pop = current_pop * ((1 + sim_pop_growth/100) ** years_forecast)
    future_built = current_built * ((1 + sim_land_consumption/100) ** years_forecast)
    sim_ratio = sim_land_consumption / sim_pop_growth if sim_pop_growth != 0 else 0
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Projected Pop (2030)", format_num(future_pop), f"{sim_pop_growth}% /yr")
    col_b.metric("Projected Built-up (2030)", f"{format_num(future_built)} km²", f"{sim_land_consumption}% /yr")
    col_c.metric("Projected SDG Ratio", f"{sim_ratio:.2f}", 
                 delta="Sustainable" if sim_ratio <= 1 else "Inefficient", delta_color="inverse")

# === TAB 4: METHODOLOGY ===
with tab4:
    st.markdown("### Methodology & Data Pipeline")
    st.markdown("""
    **1. Geospatial Database Construction**
    * **Vector Layers:** Sourced from `regions.geojson` containing administrative boundaries.
    * **Raster Processing:** Sentinel-2 imagery processed in Google Earth Engine.
    
    **2. Classification**
    * **Algorithm:** Random Forest (Supervised Learning).
    * **Validation:** Ground truth verification.
    
    **3. SDG Formula**
    $$LCRPGR = \\frac{\\ln(Urb_{t+n}/Urb_t)}{\\ln(Pop_{t+n}/Pop_t)}$$
    """)
