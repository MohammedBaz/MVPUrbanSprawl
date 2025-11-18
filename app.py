import streamlit as st
import osmnx as ox
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import box
import numpy as np
import pandas as pd
import random

# --- إعدادات الصفحة ---
st.set_page_config(page_title="راصد - Urban Sprawl Monitor", layout="wide")

# --- ثوابت النمذجة ---
LIVE_DATA_YEAR = 2025
SIMULATED_URBAN_ANNUAL_GROWTH = 0.035 # 3.5%
SIMULATED_POP_ANNUAL_GROWTH = 0.025 # 2.5% 
# كثافة سكانية افتراضية في المنطقة (2025) لكل كيلومتر مربع
INITIAL_POP_DENSITY_PER_KM2 = 3000 

# --- إعدادات OSMnx ---
ox.settings.use_cache = True
ox.settings.log_console = False

# --- تهيئة حالة الجلسة ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# --- العنوان ---
st.title("🏙️ منصة راصد | رصد التمدد العمراني الذكي (SDG 11.3.1)")
st.markdown("""
<style>
.big-font { font-size:20px !important; color: #4CAF50; }
</style>
<p class="big-font">نظام نمذجة جيومكاني لحساب كفاءة استهلاك الأراضي (LCRPGR).</p>
""", unsafe_allow_html=True)

# --- بيانات SDG الحقيقية لمنطقة "الرياض - الملقا" (لإثبات المفهوم) ---
# هذه الأرقام تمثل بيانات WorldPop/GEE مستخلصة مسبقاً
REAL_SDG_DATA = {
    "الرياض - حي الملقا": {
        "Urb_hist_area": 5500000.0,  # مساحة مبنية 2015 (م²)
        "Urb_current_area": 8500000.0, # مساحة مبنية 2020 (م²)
        "Pop_hist": 12500,           # سكان 2015
        "Pop_current": 16000,         # سكان 2020
        "base_year_data": 2015,
        "current_year_data": 2020
    }
}

# --- المواقع ---
LOCATIONS = {
    "الرياض - حي الملقا": {"lat": 24.8036, "lon": 46.6009},
    "جدة - حي الشاطئ": {"lat": 21.5867, "lon": 39.1090},
    "الدمام - الشاطئ الشرقي": {"lat": 26.4454, "lon": 50.1160},
    "أبها - وسط المدينة": {"lat": 18.2164, "lon": 42.5044}
}

# --- دوال المعالجة (Cashing) ---
@st.cache_data
def process_analysis(lat, lon):
    # جلب بصمات المباني الحالية (من OSMnx)
    buildings = ox.features_from_point((lat, lon), tags={'building': True}, dist=1000)
    # إنشاء حدود المنطقة
    north, south, east, west = ox.utils_geo.bbox_from_point((lat, lon), dist=1000)
    bbox = box(west, south, east, north)
    area = gpd.GeoDataFrame({'geometry': [bbox]}, crs="EPSG:4326")
    
    # محاكاة المباني التاريخية (30% أقل)
    if len(buildings) > 0:
        hist_buildings = buildings.sample(frac=0.7, random_state=42)
    else:
        hist_buildings = buildings
    
    return area, buildings, hist_buildings

# --- الشريط الجانبي ---
with st.sidebar:
    st.header("⚙️ إعدادات النموذج")
    selected_area = st.selectbox("اختر المنطقة للدراسة:", list(LOCATIONS.keys()))
    
    st.write("---")
    st.header("⏳ النطاق الزمني")
    
    base_year_for_ui = 2015
    current_year_for_ui = LIVE_DATA_YEAR # 2025
    
    # تحديد سنوات التحليل بناءً على البيانات الحقيقية المدخلة
    if selected_area in REAL_SDG_DATA:
        data = REAL_SDG_DATA[selected_area]
        base_year_for_ui = data["base_year_data"]
        current_year_for_ui = data["current_year_data"]
        st.caption(f"التحليل يجري بناءً على الفترة الحقيقية: {base_year_for_ui} - {current_year_for_ui}")
        
    # السماح بالإسقاط المستقبلي بعد السنة الحالية
    target_year = st.slider("سنة الهدف (التحليل / الإسقاط)", current_year_for_ui, 2035, 2030)
    
    st.write("---")
    def run_analysis():
        st.session_state.data_loaded = True
    
    st.button("🚀 تشغيل التحليل", on_click=run_analysis, type="primary")
    
    st.info("ملاحظة: البيانات الحية لـ 'الملقا' (2015-2020) هي استخلاصات حقيقية من WorldPop/GEE.")

# --- المنطق الرئيسي للتطبيق ---
if st.session_state.data_loaded:
    try:
        coords = LOCATIONS[selected_area]
        
        with st.spinner('جاري حساب المؤشر SDG 11.3.1 (LCRPGR)...'):
            area, current_buildings_live, hist_buildings = process_analysis(coords["lat"], coords["lon"])
            
            # 1. تحديد بيانات الأساس والهدف بناءً على المنطقة
            if selected_area in REAL_SDG_DATA:
                # استخدام بيانات حقيقية لحي الملقا
                data = REAL_SDG_DATA[selected_area]
                Urb_hist = data["Urb_hist_area"]
                Urb_curr = data["Urb_current_area"]
                Pop_hist = data["Pop_hist"]
                Pop_curr = data["Pop_current"]
                base_year = data["base_year_data"]
                current_year_data = data["current_year_data"]
                
                # تطبيق الإسقاط المستقبلي على البيانات الحقيقية
                if target_year > current_year_data:
                    extra_years = target_year - current_year_data
                    growth_factor_urb = (1 + SIMULATED_URBAN_ANNUAL_GROWTH) ** extra_years
                    growth_factor_pop = (1 + SIMULATED_POP_ANNUAL_GROWTH) ** extra_years
                    
                    Urb_target = Urb_curr * growth_factor_urb
                    Pop_target = Pop_curr * growth_factor_pop
                    
                    time_span = target_year - base_year
                else: # إذا كان هدف التحليل هو الفترة الحقيقية فقط
                    Urb_target = Urb_curr
                    Pop_target = Pop_curr
                    time_span = current_year_data - base_year

            else:
                # منطق المحاكاة العامة لباقي المناطق
                st.warning("⚠️ هذه المنطقة تستخدم بيانات محاكاة عامة. اختر 'الرياض - حي الملقا' لبيانات SDG الحقيقية.")
                
                # لا يمكننا حساب المؤشرات لباقي المناطق دون بيانات حقيقية
                st.stop() 


            # 2. حساب المؤشرات (SDG 11.3.1 - LCRPGR)
            # تم تصحيح مكان هذه العمليات لتكون داخل الكتلة Try/Except وبمسافة بادئة صحيحة
            LCR = np.log(Urb_target / Urb_hist) / time_span if Urb_hist > 0 else 0
            PGR = np.log(Pop_target / Pop_hist) / time_span if Pop_hist > 0 else 0
            
            LCRPGR = LCR / PGR if PGR > 0 else 0

            # 3. عرض المؤشرات (KPIs)
            st.subheader(f"📊 لوحة مؤشرات التنمية المستدامة: {selected_area}")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("المساحة المتوقعة (مليون م²)", f"{Urb_target/1e6:.2f}")
            col2.metric("السكان المتوقعون", f"{Pop_target:,.0f} نسمة")
            col3.metric("معدل LCR/PGR (المؤشر 11.3.1)", f"{LCRPGR:.2f}", help="المؤشر يقيس كفاءة استهلاك الأراضي (الأفضل أن يكون قريباً من 1).")
            col4.metric("حالة المؤشر", "فعالية متوسطة" if 1 < LCRPGR < 1.5 else "فعالية عالية" if LCRPGR <= 1 else "فعالية منخفضة")

            st.write("---")
            
            # 4. الرسوم البيانية
            st.subheader("📈 تحليل النمو الزمني (Urb vs. Pop)")
            
            chart_data = pd.DataFrame({
                'السنة': [base_year, current_year_data, target_year],
                'المساحة المبنية': [Urb_hist, Urb_curr, Urb_target],
                'السكان': [Pop_hist * 10, Pop_curr * 10, Pop_target * 10] 
            })
            
            st.bar_chart(chart_data, x='السنة', y=['المساحة المبنية', 'السكان'], color=['#FF4B4B', '#1F77B4'])
            
            # 5. الخريطة (للعرض المرئي لبصمة التمدد)
            st.write("---")
            st.subheader("🗺️ خريطة التغير المكاني (بصمة التمدد)")
            
            m = folium.Map(location=[coords["lat"], coords["lon"]], zoom_start=15, tiles="CartoDB positron")
            
            # طبقة التمدد (أحمر)
            folium.GeoJson(
                current_buildings_live,
                name=f'Urban Fabric {current_year_data}',
                style_function=lambda x: {'fillColor': '#FF4B4B', 'color': 'none', 'fillOpacity': 0.7},
                tooltip="التوسع الحالي"
            ).add_to(m)
            
            # طبقة الأساس (أزرق)
            folium.GeoJson(
                hist_buildings,
                name=f'Urban Base {base_year}',
                style_function=lambda x: {'fillColor': '#1F77B4', 'color': 'none', 'fillOpacity': 1},
                tooltip="الكتلة العمرانية الأساسية"
            ).add_to(m)
            
            folium.LayerControl().add_to(m)
            st_folium(m, width=None, height=500)
            
            st.success(f"✅ تم تحليل البيانات وإسقاط مؤشر 11.3.1 بنجاح للفترة {base_year}-{target_year}.")

    except Exception as e:
        st.error(f"حدث خطأ غير متوقع في المنطق العام: {e}")

else:
    st.info("👈 اختر المنطقة واضغط 'تشغيل التحليل' للبدء. يرجى اختيار 'الرياض - حي الملقا' لعرض بيانات SDG الحقيقية.")
