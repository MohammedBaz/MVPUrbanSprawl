# app.py - ULTIMATE PROFESSIONAL VERSION (corrected)
# Tested fixes: robust data loading, gif/raw Github URLs, error handling, graceful fallbacks.
# Requires: streamlit, pandas, plotly, requests
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO

st.set_page_config(page_title="SDG 11.3.1 Riyadh & Jeddah", layout="wide")

# ---------- Helpers ----------
def github_raw(url: str) -> str:
    """
    Ensure GitHub raw URLs return file content.
    If url already has ?raw=1, return unchanged.
    """
    if "?raw=1" in url:
        return url
    if "raw.githubusercontent.com" in url:
        return url + "?raw=1"
    # convert normal github url to raw if user accidentally uses a blob url
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/") + "?raw=1"
    return url

@st.cache_data(ttl=3600)
def load_csv_from_github(url: str) -> pd.DataFrame:
    """
    Load CSV from GitHub raw link with fallback and simple validation.
    Caches result for 1 hour.
    """
    url = github_raw(url)
    try:
        df = pd.read_csv(url)
    except Exception as e:
        raise RuntimeError(f"Failed to load CSV from {url}: {e}")
    return df

def safe_image_from_url(url: str):
    """
    Try to fetch an image (gif/png/jpg) from URL and return bytes or None.
    Use a short timeout to avoid blocking.
    """
    url = github_raw(url)
    try:
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        return None
    return None

def format_num(n):
    try:
        return f"{n:,.0f}"
    except Exception:
        return str(n)

# ---------- Page header ----------
st.markdown(
    "<h1 style='text-align: center; color: #2E86C1; margin-bottom: 0px;'>"
    "MVP SDG 11.3.1: Urban Expansion in Riyadh & Jeddah"
    "</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align: center; font-size: 20px; color: #5D6D7E; margin-top: 10px;'>"
    "Data sourced from Official UN GHSL (1975–2025) | "
    "Satellite-derived built-up layers processed via Google Earth Engine<br>"
    "<strong>European Commission Joint Research Centre & UN-Habitat</strong>"
    "</p>",
    unsafe_allow_html=True
)
st.markdown("<hr style='border-top: 1px solid #bbb; margin: 20px 0;'>", unsafe_allow_html=True)

# ---------- Controls ----------
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # spacing + centered control
    st.markdown("### ")
    city = st.selectbox("Select City", ["Riyadh", "Jeddah"], index=0)

# ---------- Load Data ----------
DATA_URL = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/saudi_cities_sdg1131_1975_2025.csv?raw=1"

try:
    df_all = load_csv_from_github(DATA_URL)
except Exception as e:
    st.error("Unable to load dataset. Please check the data source or your internet connection.")
    st.exception(e)
    st.stop()

# Basic validation
required_columns = [
    "City",
    "Built-up 1975 (km²)",
    "Built-up 1990 (km²)",
    "Built-up 2000 (km²)",
    "Built-up 2015 (km²)",
    "Built-up 2020 (km²)",
    "Built-up 2025 (km²)",
    "Population 2025",
    "SDG 11.3.1 Ratio (2020-25)",
    "Growth Type 2025"
]
missing = [c for c in required_columns if c not in df_all.columns]
if missing:
    st.error(f"The dataset is missing required columns: {missing}")
    st.stop()

# Filter for the two cities
df = df_all[df_all["City"].isin(["Riyadh", "Jeddah"])].reset_index(drop=True)
if df.empty:
    st.error("No data found for Riyadh or Jeddah in the provided dataset.")
    st.stop()

# Find selected row safely
row_candidates = df[df["City"] == city]
if row_candidates.empty:
    st.error(f"No row found for city: {city}")
    st.stop()
row = row_candidates.iloc[0]

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Historical Growth", "Expansion Animation", "Advanced Metrics"])

# ---------- Tab 1: Overview ----------
with tab1:
    st.markdown(f"### {city} – Key Indicators 2025")
    c1, c2, c3, c4 = st.columns(4)
    try:
        built_2025 = row["Built-up 2025 (km²)"]
        pop_2025 = row["Population 2025"]
        sdg_ratio = row["SDG 11.3.1 Ratio (2020-25)"]
        growth_type = row.get("Growth Type 2025", "Unknown")
    except Exception:
        st.error("Selected city row missing expected fields.")
        st.stop()

    c1.metric("Built-up Area (2025)", f"{format_num(built_2025)} km²")
    c2.metric("Population (2025)", f"{format_num(pop_2025)}")
    if pd.isna(sdg_ratio):
        c3.metric("SDG 11.3.1 Ratio (2020-25)", "N/A")
        st.warning("SDG 11.3.1 ratio is missing for this city.")
    else:
        c3.metric("SDG 11.3.1 Ratio (2020-25)", f"{sdg_ratio:.3f}")
    c4.metric("Growth Pattern", growth_type)

    st.markdown("#### Notes")
    st.markdown(
        "- Built-up areas are derived from GHSL layers processed in Google Earth Engine.\n"
        "- SDG 11.3.1: ratio of land consumption rate to population growth rate (values close to 1 indicate sustainable/compact growth)."
    )

# ---------- Tab 2: Historical Growth ----------
with tab2:
    st.markdown("### Built-up Area Growth 1975–2025")
    years = [1975, 1990, 2000, 2015, 2020, 2025]
    # Build values defensively
    built_vals = []
    for y in years:
        colname = f"Built-up {y} (km²)"
        val = row.get(colname, None)
        if pd.isna(val):
            built_vals.append(None)
        else:
            built_vals.append(float(val))

    # Create DataFrame for plotly (drop missing)
    df_plot = pd.DataFrame({"year": years, "built_km2": built_vals}).dropna()
    if df_plot.empty:
        st.warning("Not enough historical built-up data to draw the chart.")
    else:
        fig = px.line(df_plot, x="year", y="built_km2", markers=True, line_shape="spline",
                      labels={"year": "Year", "built_km2": "Built-up area (km²)"})
        fig.update_traces(line=dict(color="#d62728", width=4), marker=dict(size=10))
        fig.update_layout(height=520, font=dict(size=14), yaxis=dict(tickformat=","))
        st.plotly_chart(fig, use_container_width=True)

# ---------- Tab 3: Expansion Animation ----------
with tab3:
    st.markdown("### Urban Expansion 2020 → 2025")
    st.markdown("*Dark red = 2020 built-up | Bright red = new development by 2025*")

    col_img, col_stats = st.columns([2, 1])

    with col_img:
        gif_file = "Riyadh_expansion.gif" if city == "Riyadh" else "Jeddah_expansion.gif"
        gif_url = f"https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/{gif_file}?raw=1"
        gif_bytes = safe_image_from_url(gif_url)

        if gif_bytes:
            try:
                st.image(gif_bytes, use_column_width=True)
            except Exception:
                st.warning("Could not render the animation; showing static placeholder.")
                st.image("https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/placeholder.png?raw=1",
                         use_column_width=True)
        else:
            st.info("Animation asset not available. Showing static summary.")
            # Attempt to show a static PNG if exists
            static_img_url = f"https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/{city}_expansion_static.png?raw=1"
            static_bytes = safe_image_from_url(static_img_url)
            if static_bytes:
                st.image(static_bytes, use_column_width=True)
            else:
                st.markdown("*(No image available in the repository — please add `assets/{}` to the repo.)*".format(gif_file))

    with col_stats:
        st.markdown("### Real-time Expansion Stats")
        try:
            built_2020 = float(row.get("Built-up 2020 (km²)", 0))
            built_2025 = float(row.get("Built-up 2025 (km²)", 0))
        except Exception:
            built_2020 = None
            built_2025 = None

        if built_2020 in (None, 0) or built_2025 in (None, 0):
            st.warning("Insufficient data to compute expansion statistics.")
            if built_2020 == 0 and built_2025 != 0:
                st.metric("New Built-up Area", f"+{format_num(built_2025)} km²")
            else:
                st.metric("New Built-up Area", "N/A")
            st.metric("Growth Rate (5 years)", "N/A")
            st.metric("Annual Land Consumption", "N/A")
        else:
            new_area = built_2025 - built_2020
            # Avoid division by zero
            growth_pct = (new_area / built_2020) * 100 if built_2020 != 0 else float("nan")
            annual_consumption = new_area / 5.0
            st.metric("New Built-up Area", f"+{format_num(new_area)} km²")
            st.metric("Growth Rate (5 years)", f"+{growth_pct:.1f}%")
            st.metric("Annual Land Consumption", f"{annual_consumption:,.2f} km²/year")
            interpretation = "Compact & Sustainable" if growth_pct < 20 else "Moderate Sprawl" if growth_pct < 40 else "Significant Sprawl"
            st.markdown(f"**Assessment**: {interpretation}")

# ---------- Tab 4: Advanced Metrics ----------
with tab4:
    st.markdown("### Riyadh vs Jeddah – SDG 11.3.1 Comparison")
    try:
        fig = px.bar(df, x="City", y="SDG 11.3.1 Ratio (2020-25)", color="Growth Type 2025",
                     color_discrete_map={"Sprawl": "#e74c3c", "Balanced": "#f39c12", "Compact": "#27ae60"},
                     text="SDG 11.3.1 Ratio (2020-25)", height=520)
        fig.add_hline(y=1.0, line_dash="dash", line_color="white",
                      annotation_text="Ideal sustainable growth = 1.0", annotation_position="top left")
        fig.update_traces(textposition="outside", texttemplate="%{text:.2f}", textfont_size=14)
        fig.update_layout(yaxis_title="SDG 11.3.1 Ratio", xaxis_title="City", uniformtext_minsize=12)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Failed to draw comparison chart.")
        st.exception(e)

    st.markdown("#### Additional details")
    st.markdown(
        "- The dashed line at 1.0 represents an ideal balance between land consumption and population growth.\n"
        "- Values above 1 indicate higher land consumption relative to population growth (potential sprawl)."
    )

# ---------- Footer ----------
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Project completed 19 Nov 2025 | Data source: GHSL P2023A | Built by Mohammed Baz</p>", unsafe_allow_html=True)
