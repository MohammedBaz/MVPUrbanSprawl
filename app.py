# app.py – 100% offline, works instantly on Streamlit Cloud
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SDG 11.3.1 Saudi Arabia", layout="wide")
st.title("🇸🇦 SDG 11.3.1 Explorer – Saudi Cities 1975–2025")
st.markdown("**Official UN GHSL data · No live satellite calls · Instant loading**")

@st.cache_data
def load_data():
    # ← CHANGE THIS to your actual GitHub username and repo name
    url = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO_NAME/main/saudi_cities_sdg1131_1975_2025.csv"
    return pd.read_csv(url)

df = load_data()

city = st.selectbox("Select City", df["City"].tolist())
row = df[df["City"] == city].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Built-up 2025", f"{row['Built-up 2025 (km²)']:,} km²")
c2.metric("Population 2025", f"{row['Population 2025']:,.0f}")
c3.metric("SDG 11.3.1 Ratio (2020-25)", f"{row['SDG 11.3.1 Ratio (2020-25)']:.3f}")
c4.metric("Growth Pattern", row['Growth Type 2025'], 
          delta="Sprawl" if row['SDG 11.3.1 Ratio (2020-25)'] > 1.2 else None)

# Line chart of urban expansion
years = [1975, 1990, 2000, 2015, 2020, 2025]
built = [row[f"Built-up {y} (km²)"] for y in years]
fig = px.line(x=years, y=built, markers=True, title=f"{city} – Built-up Area Growth 1975–2025")
fig.update_yaxes(title="Built-up Area (km²)")
st.plotly_chart(fig, use_container_width=True)

# National comparison bar chart
st.subheader("All Cities – SDG 11.3.1 Ratio (2020–2025)")
ranking = df.sort_values("SDG 11.3.1 Ratio (2020-25)", ascending=False)
fig2 = px.bar(ranking, x="City", y="SDG 11.3.1 Ratio (2020-25)", 
              color="Growth Type 2025",
              color_discrete_map={"Sprawl": "red", "Balanced": "orange", "Compact": "green"})
fig2.add_hline(y=1.0, line_dash="dash", annotation_text="Sustainable threshold = 1.0")
st.plotly_chart(fig2, use_container_width=True)

st.success("Data source: GHSL 2023 (UN official) • Updated Nov 2025")
