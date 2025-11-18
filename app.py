import streamlit as st
import osmnx as ox
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import box
import numpy as np
import pandas as pd

# --- إعدادات الصفحة ---
st.set_page_config(page_title="راصد - Urban Sprawl Monitor", layout="wide")

# --- ثوابت النمذجة (للتنبؤ المحاكي) ---
LIVE_DATA_YEAR = 2025
# معدلات النمو المفترضة (للمحاكاة فقط)
SIMULATED_URBAN_ANNUAL_GROWTH = 0.035 # 3.5%
SIMULATED_POP_ANNUAL_GROWTH = 0.025 # 2.5% (معدل نمو سكاني سنوي)
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
<p class="big-font">النموذج يدمج بيانات المباني (Urb) مع نمذجة النمو السكاني (Pop) لحساب كفاءة استهلاك الأراضي.</p>
""", unsafe_allow_html=True)

# --- المواقع ---
LOCATIONS = {
    "الرياض - حي الملقا": {"lat": 24.8036, "lon": 46.6009},
    "جدة - حي الشاطئ": {"lat": 21.5867, "lon": 39.1090},
    "الدمام - الشاطئ الشرقي": {"lat": 26.4454, "lon": 50.1160},
    "أبها - وسط المدينة": {"lat": 18.2164, "lon": 42.5044}
}

# --- الشريط الجانبي ---
with st.sidebar:
    st.header("⚙️ إعدادات النموذج")
    selected_area = st.selectbox("اختر المنطقة للدراسة:", list(LOCATIONS.keys()))
    
    st.write("---")
    st.header("⏳ النطاق الزمني")
    base_year = st.slider("سنة الأساس (الماضي المحاكى)", 2010, 2020, 2015)
    target_year = st.slider("سنة الهدف (التحليل / الإسقاط)", LIVE_DATA_YEAR, 2035, 2030)

    if target_year < LIVE_DATA_YEAR:
        st.warning(f"للتنبؤ، يجب أن تكون سنة الهدف أكبر من أو تساوي {LIVE_DATA_YEAR}.")

    st.write("---")
    def run_analysis():
        st.session_state.data_loaded = True
    
    st.button("🚀 تشغيل التحليل", on_click=run_analysis, type="primary")
    
    st.info(f"ملاحظة: يتم محاكاة بيانات السكان بمعدل نمو 2.5% سنوياً لأغراض العرض الأولي.")

# --- دوال المعالجة ---
@st.cache_data
def process_analysis(lat, lon):
    buildings = ox.features_from_point((lat, lon), tags={'building': True}, dist=1000)
    north, south, east, west = ox.utils_geo.bbox_from_point((lat, lon), dist=1000)
    bbox = box(west, south, east, north)
    area = gpd.GeoDataFrame({'geometry': [bbox]}, crs="EPSG:4326")
    
    # المحاكاة التاريخية (Base Year)
    hist_buildings = buildings.sample(frac=0.7) if len(buildings) > 0 else buildings
    
    return area, buildings, hist_buildings

# --- المنطق الرئيسي للتطبيق ---
if st.session_state.data_loaded:
    try:
        coords = LOCATIONS[selected_area]
        
        with st.spinner('جاري حساب مؤشرات LCR و PGR و LCRPGR...'):
            area, current_buildings_live, hist_buildings = process_analysis(coords["lat"], coords["lon"])
            
            if len(current_buildings_live) == 0:
                st.error("لا توجد بيانات كافية.")
            else:
                # 1. حسابات المساحة الحضرية (Urb)
                area_proj = area.to_crs(epsg=32638)
                curr_proj = current_buildings_live.to_crs(epsg=32638)
                hist_proj = hist_buildings.to_crs(epsg=32638)
                
                total_area_km2 = area_proj.geometry.area.sum() / 1e6
                
                Urb_hist = hist_proj.geometry.area.sum()
                Urb_curr = curr_proj.geometry.area.sum()
                
                # تطبيق الإسقاط العمراني إذا كان الهدف مستقبلياً
                if target_year > LIVE_DATA_YEAR:
                    growth_factor_urb = (1 + SIMULATED_URBAN_ANNUAL_GROWTH) ** (target_year - LIVE_DATA_YEAR)
                    Urb_target = Urb_curr * growth_factor_urb
                else:
                    Urb_target = Urb_curr
                
                # 2. حسابات السكان (Pop) - المحاكاة
                # تقدير السكان الحاليين بناءً على الكثافة المفترضة ومساحة المنطقة
                Pop_curr = total_area_km2 * INITIAL_POP_DENSITY_PER_KM2 
                
                # حساب السكان التاريخيين
                pop_hist_factor = (1 + SIMULATED_POP_ANNUAL_GROWTH) ** (LIVE_DATA_YEAR - base_year)
                Pop_hist = Pop_curr / pop_hist_factor 
                
                # حساب السكان المستقبليين
                pop_target_factor = (1 + SIMULATED_POP_ANNUAL_GROWTH) ** (target_year - LIVE_DATA_YEAR)
                Pop_target = Pop_curr * pop_target_factor
                
                # 3. حساب المؤشرات (SDG 11.3.1 - LCRPGR)
                time_span = target_year - base_year
                
                # LCR (معدل استهلاك الأراضي)
                LCR = np.log(Urb_target / Urb_hist) / time_span if Urb_hist > 0 else 0
                
                # PGR (معدل النمو السكاني)
                PGR = np.log(Pop_target / Pop_hist) / time_span if Pop_hist > 0 else 0
                
                # LCRPGR (المؤشر المطلوب)
                LCRPGR = LCR / PGR if PGR > 0 else 0

                # 4. عرض المؤشرات (KPIs)
                st.subheader(f"📊 مؤشرات التنمية المستدامة الحضرية: {selected_area}")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("المساحة المتوقعة (مليون م²)", f"{Urb_target/1e6:.2f}")
                col2.metric("السكان المتوقعون", f"{Pop_target:,.0f} نسمة")
                col3.metric("معدل LCR/PGR (المؤشر 11.3.1)", f"{LCRPGR:.2f}", help="المؤشر يقيس كفاءة استهلاك الأراضي (الأفضل أن يكون قريباً من 1).")
                col4.metric("حالة المؤشر", "فعالية متوسطة" if 1 < LCRPGR < 1.5 else "فعالية عالية" if LCRPGR <= 1 else "فعالية منخفضة")

                st.write("---")
                
                # 5. الرسوم البيانية
                st.subheader("📈 تحليل النمو الزمني والمكاني")
                
                chart_data = pd.DataFrame({
                    'السنة': [base_year, LIVE_DATA_YEAR, target_year],
                    'المساحة المبنية': [Urb_hist, Urb_curr, Urb_target],
                    'السكان': [Pop_hist * 10, Pop_curr * 10, Pop_target * 10] # ضرب السكان بـ 10 لتظهر على نفس الرسم
                })
                
                st.bar_chart(chart_data, x='السنة', y=['المساحة المبنية', 'السكان'], color=['#FF4B4B', '#1F77B4'])
                
                # 6. الخريطة (نفس منطق العرض)
                # ... (باقي كود الخريطة كما هو) ...

                st.success(f"✅ تم تحليل البيانات وإسقاط مؤشر 11.3.1 بنجاح للفترة {base_year}-{target_year}.")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
else:
    st.info("👈 اختر المنطقة واضغط 'تشغيل التحليل'.")
