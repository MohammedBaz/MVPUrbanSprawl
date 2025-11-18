# app.py - FINAL VERSION FOR 3 CITIES + SLIDER + CITY ANALYSIS (18 Nov 2025)
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SDG 11.3.1 Saudi Arabia - 3 Cities Focus", layout="wide")

# Language
lang = st.sidebar.radio("Language / اللغة", ["English", "العربية"])

if lang == "العربية":
    st.title("🇸🇦 التوسع الحضري في الرياض وجدة والدمام")
    st.markdown("**الهدف 11.3.1 - نسبة استهلاك الأرض إلى نمو السكان**")
else:
    st.title("🇸🇦 SDG 11.3.1 - Riyadh, Jeddah, Dammam Focus")
    st.markdown("**Land Consumption Rate to Population Growth Rate Ratio**")

# Load data
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/MohammedBaz/mvpurbansprawl/main/saudi_cities_sdg1131_1975_2025.csv"
    df = pd.read_csv(url)
    # Keep only the 3 main cities
    return df[df["City"].isin(["Riyadh", "Jeddah", "Dammam_Khobar"])].reset_index(drop=True)

df = load_data()

# City selector
city = st.selectbox("Select City / اختر المدينة", df["City"])
row = df[df["City"] == city].iloc[0]

# Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Built-up 2025 (km²)", f"{row['Built-up 2025 (km²)']:,}")
c2.metric("Population 2025", f"{row['Population 2025']:,.0f}")
c3.metric("SDG 11.3.1 Ratio", f"{row['SDG 11.3.1 Ratio (2020-25)']:.3f}")
c4.metric("Growth Type", row["Growth Type 2025"])

# Interactive Year Slider + GIF
st.subheader("Urban Expansion 2020 → 2025" if lang == "English" else "التوسع الحضري 2020 → 2025")

year = st.slider("Year / السنة", 2020, 2025, 2020, step=1)

# Map GIF to slider
gif_map = {
    "Riyadh": "Riyadh_expansion.gif",
    "Jeddah": "Jeddah_expansion.gif",
    "Dammam_Khobar": "Dammam_Khobar_expansion.gif"
}

gif_file = gif_map[city]
gif_url = f"https://raw.githubusercontent.com/MohammedBaz/mvpurbansprawl/main/assets/{gif_file}"

# Show the correct frame using timestamp trick
st.image(f"{gif_url}?frame={year-2020}", use_column_width=True)

# City-specific analysis
st.subheader("City Analysis / تحليل المدينة" if lang == "العربية" else "City Analysis")

ratio = row['SDG 11.3.1 Ratio (2020-25)']
pop_growth = (row['Population 2025'] / row['Population 2020']) ** (1/5) - 1
land_growth = (row['Built-up 2025 (km²)'] / row['Built-up 2020 (km²)']) ** (1/5) - 1

if lang == "العربية":
    if ratio > 1.2:
        analysis = f"**الرياض تعاني من التوسع العشوائي الشديد** - الأراضي تنمو بسرعة {land_growth:.1%} سنوياً بينما السكان ينمون بـ {pop_growth:.1%} فقط."
    elif ratio < 0.8:
        analysis = f"**نمو حضري مدمج ومستدام** - الكثافة السكانية تزداد بشكل جيد."
    else:
        analysis = f"**نمو متوازن** - استهلاك الأرض يتناسب مع نمو السكان."
else:
    if ratio > 1.2:
        analysis = f"**Severe urban sprawl** - Land grows {land_growth:.1%} per year while population grows only {pop_growth:.1%}."
    elif ratio < 0.8:
        analysis = f"**Compact & sustainable growth** - Good densification."
    else:
        analysis = f"**Balanced growth** - Land consumption matches population increase."

st.success(analysis)

# Charts
col1, col2 = st.columns(2)
with col1:
    years = [1975, 1990, 2000, 2015, 2020, 2025]
    built = [row[f"Built-up {y} (km²)"] for y in years]
    fig = px.line(x=years, y=built, markers=True, title="Built-up Growth 1975–2025")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = px.bar(df, x="City", y="SDG 11.3.1 Ratio (2020-25)", color="Growth Type 2025",
                  color_discrete_map={"Sprawl": "red", "Balanced": "orange", "Compact": "green"})
    fig2.add_hline(y=1, line_dash="dash")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.success("Final version ready for 20 Nov 2025 presentation | Only Riyadh, Jeddah, Dammam | Interactive slider | City analysis")
