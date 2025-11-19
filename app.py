"""
streamlit_satellite_interactive_app.py
Interactive Streamlit app for satellite imagery + metrics
Features included:
- City & year selector
- Timeline slider + play/pause animation
- Layer toggles (built-up, NDVI, change heatmap)
- Side-by-side comparison (DualMap)
- Draw AOI and compute simple aggregated metrics from CSV
- Click-to-inspect (pixel/time-series pop-up) using precomputed CSV

NOTES / TODOs:
- This example uses static image overlays stored in a GitHub repo (assets/...).
- Replace image URLs with actual WMS/Tile endpoints or precomputed tiles for production.
- Requires packages: streamlit, pandas, requests, folium, streamlit_folium, plotly

Run:
    pip install -r requirements.txt
    streamlit run streamlit_satellite_interactive_app.py

"""

import streamlit as st
import pandas as pd
import time
import requests
from io import BytesIO
import plotly.express as px
import folium
from folium.raster_layers import ImageOverlay
from folium.plugins import Draw, DualMap
from streamlit_folium import st_folium

st.set_page_config(page_title="Interactive Satellite Explorer", layout="wide")

# --------------------------- Helper functions ---------------------------

def github_raw(url: str) -> str:
    if "?raw=1" in url:
        return url
    if "raw.githubusercontent.com" in url:
        return url + "?raw=1"
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/") + "?raw=1"
    return url


def fetch_image_bytes(url: str, timeout: int = 6):
    """Return bytes or None"""
    url = github_raw(url)
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.content
    except Exception:
        return None
    return None


def load_metrics_csv(url: str) -> pd.DataFrame:
    url = github_raw(url)
    return pd.read_csv(url)


# --------------------------- Configuration ---------------------------
ASSETS_BASE = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/"
DATA_CSV = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/saudi_cities_sdg1131_1975_2025.csv?raw=1"

# Years for which we have imagery (for demonstration)
YEARS = [2014, 2015, 2020, 2025]

# bounding box for image overlays (lat/lon) - replace with your AOI bounds
# Riyadh example bbox (min_lat, min_lon, max_lat, max_lon)
BBOXES = {
    "Riyadh": [21.3, 39.0, 21.8, 39.6],
    "Jeddah": [21.4, 39.0, 21.9, 39.7]
}

# --------------------------- Load data ---------------------------
st.sidebar.markdown("## Data & Controls")
try:
    df_metrics = load_metrics_csv(DATA_CSV)
except Exception as e:
    st.sidebar.error("Failed to load metrics CSV. The app will still run with placeholders.")
    df_metrics = pd.DataFrame()

# --------------------------- UI Controls ---------------------------
city = st.sidebar.selectbox("City", ["Riyadh", "Jeddah"], index=0)
start_year = st.sidebar.selectbox("Start year", YEARS, index=0)
end_year = st.sidebar.selectbox("End year", YEARS, index=len(YEARS)-1)
if YEARS.index(start_year) > YEARS.index(end_year):
    st.sidebar.error("Start year must be <= end year")

# Layer toggles
st.sidebar.markdown("### Layers")
show_built = st.sidebar.checkbox("Built-up layer", value=True)
show_ndvi = st.sidebar.checkbox("NDVI layer", value=False)
show_change = st.sidebar.checkbox("Change heatmap", value=False)

# Timeline controls
st.sidebar.markdown("### Timeline")
year_index = st.sidebar.slider("Select year", 0, len(YEARS)-1, len(YEARS)-1)
play = st.sidebar.button("Play")

# AOI tools
st.sidebar.markdown("### Area of Interest")
show_draw = st.sidebar.checkbox("Enable AOI drawing", value=True)

# --------------------------- Main layout ---------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("# Interactive Satellite Map")

    # Create an interactive DualMap for side-by-side comparison
    left_map = folium.Map(location=[(BBOXES[city][0]+BBOXES[city][2])/2, (BBOXES[city][1]+BBOXES[city][3])/2], zoom_start=10)
    right_map = folium.Map(location=[(BBOXES[city][0]+BBOXES[city][2])/2, (BBOXES[city][1]+BBOXES[city][3])/2], zoom_start=10)

    dual = DualMap(location=[(BBOXES[city][0]+BBOXES[city][2])/2, (BBOXES[city][1]+BBOXES[city][3])/2], zoom_start=10)

    # add image overlays for the selected years
    year_left = YEARS[year_index]
    year_right = end_year

    left_url = f"{ASSETS_BASE}{city}_built_{year_left}.png"
    right_url = f"{ASSETS_BASE}{city}_built_{year_right}.png"

    left_bytes = fetch_image_bytes(left_url)
    right_bytes = fetch_image_bytes(right_url)

    # If image bytes available, add as ImageOverlay
    bounds = [[BBOXES[city][0], BBOXES[city][1]], [BBOXES[city][2], BBOXES[city][3]]]
    if left_bytes:
        io_left = BytesIO(left_bytes)
        ImageOverlay(image=io_left, bounds=bounds, opacity=0.7).add_to(dual.m1)
    else:
        folium.TileLayer().add_to(dual.m1)

    if right_bytes:
        io_right = BytesIO(right_bytes)
        ImageOverlay(image=io_right, bounds=bounds, opacity=0.7).add_to(dual.m2)
    else:
        folium.TileLayer().add_to(dual.m2)

    # Add draw control to left map if enabled
    draw = Draw(export=True)
    draw.add_to(dual.m1)

    # Add a marker cluster / optional tools
    folium.LayerControl().add_to(dual.m1)
    folium.LayerControl().add_to(dual.m2)

    # Render the dual map and capture interaction data
    st.write("\n**Side-by-side: left = selected year, right = comparison year**\n")
    map_data = st_folium(dual, width=900, height=600)

    # map_data contains keys like 'last_clicked', 'all_drawings'
    last_clicked = map_data.get("last_clicked")
    drawings = map_data.get("all_drawings")

    if last_clicked:
        lat = last_clicked["lat"]
        lon = last_clicked["lng"]
        st.sidebar.markdown("### Click inspector")
        st.sidebar.write(f"lat: {lat:.5f}, lon: {lon:.5f}")

        # Mock: build a small time series using values from df_metrics (if present)
        if not df_metrics.empty:
            city_row = df_metrics[df_metrics["City"] == city]
            if not city_row.empty:
                # create a fake pixel series from built-up area values
                times = [1975, 1990, 2000, 2015, 2020, 2025]
                vals = [city_row.iloc[0].get(f"Built-up {y} (km²)") for y in times]
                ts_df = pd.DataFrame({"year": times, "built_km2": vals})
                fig = px.line(ts_df, x="year", y="built_km2", markers=True, title=f"Time series at clicked location (approx city avg)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.sidebar.info("No city metrics row found to build a sample time series.")
        else:
            st.sidebar.info("Metrics CSV not available; cannot build time series.")

    # If AOI drawn, compute simple aggregated metrics (sum of city built-up delta as demo)
    if drawings and len(drawings) > 0:
        st.markdown("### AOI Summary")
        last_draw = drawings[-1]
        st.write("Geometry type:", last_draw.get("type"))
        st.write("GeoJSON keys:", list(last_draw.keys()))

        # Demo aggregation: use precomputed city-level metrics to show change between years
        if not df_metrics.empty:
            city_row = df_metrics[df_metrics["City"] == city]
            if not city_row.empty:
                b_start = city_row.iloc[0].get(f"Built-up {start_year} (km²)", None)
                b_end = city_row.iloc[0].get(f"Built-up {end_year} (km²)", None)
                if pd.notna(b_start) and pd.notna(b_end):
                    new_area = b_end - b_start
                    st.metric("New built-up area in AOI (approx)", f"{new_area:,.0f} km²")
                    st.write("(This is a city-level proxy. Replace with per-pixel aggregation when you have rasters / tiles.)")
                else:
                    st.info("City metrics missing for selected years.")
        else:
            st.info("No metrics CSV available to compute AOI summary.")

with col2:
    st.markdown("# Metrics & Controls")

    # Show main metrics for selected city (from CSV if available)
    if not df_metrics.empty:
        r = df_metrics[df_metrics["City"] == city]
        if not r.empty:
            r0 = r.iloc[0]
            st.metric("Built-up 2025 (km²)", f"{r0.get('Built-up 2025 (km²)', 'N/A')}")
            st.metric("Population 2025", f"{r0.get('Population 2025', 'N/A')}")
            st.metric("SDG 11.3.1 Ratio (2020-25)", f"{r0.get('SDG 11.3.1 Ratio (2020-25)', 'N/A')}")

    st.markdown("---")
    st.markdown("### Layer preview & opacity")
    opacity = st.slider("Overlay opacity", 0.1, 1.0, 0.7)

    # Layer legend & small preview images (if available)
    st.markdown("**Available imagery (preview)**")
    preview_year = st.selectbox("Preview year", YEARS, index=len(YEARS)-1)
    preview_url = f"{ASSETS_BASE}{city}_built_{preview_year}.png"
    preview_bytes = fetch_image_bytes(preview_url)
    if preview_bytes:
        st.image(preview_bytes, caption=f"{city} built {preview_year}", use_column_width=True)
    else:
        st.info("Preview image not available in repository.")

    st.markdown("---")

    # Comparison controls
    st.markdown("### Comparison")
    compare_year = st.selectbox("Compare to year", YEARS, index=0, key="compare_year")
    if st.button("Swap left/right"):
        # simple swap: swap the indices (not persistent across reruns without session state)
        temp = year_index
        year_index = YEARS.index(compare_year)
        compare_year = YEARS[temp]
        st.experimental_rerun()

    # Export buttons
    st.markdown("---")
    st.markdown("### Export & Share")
    if st.button("Download metrics CSV"):
        if not df_metrics.empty:
            csv_bytes = df_metrics.to_csv(index=False).encode("utf-8")
            st.download_button("Click to download", data=csv_bytes, file_name="metrics.csv", mime="text/csv")
        else:
            st.info("No CSV available to download.")

# --------------------------- Animation (play) ---------------------------
# lightweight play functionality: cycles through YEARS and updates the map by re-running
if play:
    for i in range(len(YEARS)):
        st.session_state['play_index'] = i
        # small sleep; in production consider more sophisticated state handling
        time.sleep(0.6)
        st.experimental_rerun()

# --------------------------- Footer ---------------------------
st.markdown("---")
st.markdown("Built by Mohammed Baz — Replace static image overlays with tiles or WMS for production.")

# --------------------------- Requirements ---------------------------
# Save a requirements.txt (example):
# streamlit
# pandas
# requests
# folium
# streamlit-folium
# plotly

