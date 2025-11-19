# app.py - FINAL PROFESSIONAL VERSION (19 Nov 2025) - English only + Metrics + Clean Design
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SDG 11.3.1 Riyadh & Jeddah", layout="wide")

# --- CLEAN TITLE ---
st.title("🇸🇦 SDG 11.3.1: Urban Expansion in Riyadh & Jeddah")
st.markdown("**Official UN GHSL Data (1975–2025) | Real-time Expansion Metrics**")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/saudi_cities_sdg1131_1975_2025.csv"
    df = pd.read_csv(url)
    return df[df["City"].isin(["Riyadh", "Jeddah"])].reset_index(drop=True)

df = load_data()

# --- SIDEBAR CONTROLS (city + optional controls) ---
with st.sidebar:
    st.header("Controls")
    city = st.selectbox("Select City", df["City"])
    st.info("Animation shows 2020 (dark red) → 2025 (bright red = new development)")

row = df[df["City"] == city].iloc[0]

# --- MAIN METRICS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Built-up Area 2025", f"{row['Built-up 2025 (km²)']:,} km²")
c2.metric("Population 2025", f"{row['Population 2025']:,.0f}")
c3.metric("SDG 11.3.1 Ratio (2020-25)", f"{row['SDG 11.3.1 Ratio (2020-25)']:.3f}")
c4.metric("Growth Pattern", row["Growth Type 2025"])

# --- ANIMATED GIF WITH REAL-TIME METRICS ---
st.subheader(f"{city} Urban Expansion 2020 → 2025")

# Calculate real expansion stats
new_area = row['Built-up 2025 (km²)'] - row['Built-up 2020 (km²)']
percent_growth = (new_area / row['Built-up 2020 (km²)']) * 100

col_left, col_right = st.columns([3, 1])

with col_left:
    gif_file = "Riyadh_expansion.gif" if city == "Riyadh" else "Jeddah_expansion.gif"
    gif_url = f"https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/{gif_file}"
    st.image(gif_url, use_column_width=True)

with col_right:
    st.markdown("### Live Expansion Stats")
    st.metric("New Built-up Area (2020-2025)", f"+{new_area:,.0f} km²")
    st.metric("Growth Rate", f"+{percent_growth:.1f}%")
    st.metric("Annual Land Consumption", f"{new_area/5:.0f} km²/year")
    st.markdown(f"**Interpretation**: {'Sprawl' if percent_growth > 30 else 'Controlled' if percent_growth > 15 else 'Compact'} growth")

# --- HISTORICAL CHART ---
st.subheader("Historical Built-up Growth (1975–2025)")
years = [1975, 1990, 2000, 2015, 2020, 2025]
built = [row[f"Built-up {y} (km²)"] for y in years]
fig = px.line(x=years, y=built, markers=True, title=f"{city} Built-up Area Over Time")
fig.update_traces(line=dict(width=4), marker=dict(size=10))
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# --- COMPARISON CHART ---
st.subheader("Riyadh vs Jeddah – SDG 11.3.1 Ratio")
fig2 = px.bar(df, x="City", y="SDG 11.3.1 Ratio (2020-25)", color="Growth Type 2025",
              color_discrete_map={"Sprawl": "#e74c3c", "Balanced": "#f39c12", "Compact": "#27ae60"},
              text="SDG 11.3.1 Ratio (2020-25)")
fig2.update_traces(textposition="outside")
fig2.add_hline(y=1.0, line_dash="dash", line_color="white", annotation_text="Ideal = 1.0")
fig2.update_layout(height=500, showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

# --- FOOTER ---
st.markdown("---")
st.success("Final Presentation Version | 19 Nov 2025 | Riyadh & Jeddah only | Real-time metrics | Professional design")
st.caption("Data source: Global Human Settlement Layer (GHSL) – European Commission & UN-Habitat | Animation: GHSL Built-up Surface 2023 Release")
