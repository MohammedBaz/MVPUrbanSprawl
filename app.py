# app.py - ULTIMATE PROFESSIONAL VERSION (19 Nov 2025) - Multi-tab + No Sidebar
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SDG 11.3.1 Riyadh & Jeddah", layout="wide")

# Title + City Selector centered
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

# Optional: add a thin line separator for extra elegance
st.markdown("<hr style='border-top: 1px solid #bbb; margin: 30px 0;'>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1,1,1])
with col2:
    city = st.selectbox("Select City", ["Riyadh", "Jeddah"], index=0)

# Load data
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/saudi_cities_sdg1131_1975_2025.csv"
    df = pd.read_csv(url)
    return df[df["City"].isin(["Riyadh", "Jeddah"])].reset_index(drop=True)

df = load_data()
row = df[df["City"] == city].iloc[0]

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Historical Growth", "Expansion Animation", "Advanced Metrics"])

with tab1:
    st.markdown(f"### {city} – Key Indicators 2025")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Built-up Area", f"{row['Built-up 2025 (km²)']:,} km²")
    c2.metric("Population", f"{row['Population 2025']:,.0f}")
    c3.metric("SDG 11.3.1 Ratio (2020-25)", f"{row['SDG 11.3.1 Ratio (2020-25)']:.3f}")
    c4.metric("Growth Pattern", row["Growth Type 2025"])

with tab2:
    st.markdown("### Built-up Area Growth 1975–2025")
    years = [1975, 1990, 2000, 2015, 2020, 2025]
    built = [row[f"Built-up {y} (km²)"] for y in years]
    fig = px.line(x=years, y=built, markers=True, line_shape='spline')
    fig.update_traces(line=dict(color="#d62728", width=6), marker=dict(size=12))
    fig.update_layout(height=600, font=dict(size=16))
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### Urban Expansion 2020 → 2025")
    st.markdown("*Dark red = 2020 built-up | Bright red = new development by 2025*")
    
    col_img, col_stats = st.columns([2,1])
    
    with col_img:
        gif_file = "Riyadh_expansion.gif" if city == "Riyadh" else "Jeddah_expansion.gif"
        gif_url = f"https://raw.githubusercontent.com/MohammedBaz/MVPUrbanSprawl/main/assets/{gif_file}"
        st.image(gif_url, use_column_width=True)
    
    with col_stats:
        st.markdown("### Real-time Expansion Stats")
        new_area = row['Built-up 2025 (km²)'] - row['Built-up 2020 (km²)']
        growth_pct = (new_area / row['Built-up 2020 (km²)']) * 100
        st.metric("New Built-up Area", f"+{new_area:,.0f} km²")
        st.metric("Growth Rate (5 years)", f"+{growth_pct:.1f}%")
        st.metric("Annual Land Consumption", f"{new_area/5:,.0f} km²/year")
        interpretation = "Compact & Sustainable" if growth_pct < 20 else "Moderate Sprawl" if growth_pct < 40 else "Significant Sprawl"
        st.markdown(f"**Assessment**: {interpretation}")

with tab4:
    st.markdown("### Riyadh vs Jeddah – SDG 11.3.1 Comparison")
    fig = px.bar(df, x="City", y="SDG 11.3.1 Ratio (2020-25)", color="Growth Type 2025",
                 color_discrete_map={"Sprawl": "#e74c3c", "Balanced": "#f39c12", "Compact": "#27ae60"},
                 text="SDG 11.3.1 Ratio (2020-25)", height=600)
    fig.add_hline(y=1.0, line_dash="dash", line_color="white", annotation_text="Ideal sustainable growth = 1.0")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Project completed 19 Nov 2025 | Data source: GHSL P2023A | Built by Mohammed Baz</p>", unsafe_allow_html=True)
