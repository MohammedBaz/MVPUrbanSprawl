import streamlit as st
import osmnx as ox
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import box

# --- إعدادات الصفحة ---
st.set_page_config(page_title="راصد - Urban Sprawl Monitor", layout="wide")

# --- ثوابت النمذجة (للتنبؤ المحاكي) ---
# نفترض أن البيانات "الحية" (OSM) تمثل عام 2025
LIVE_DATA_YEAR = 2025
# نفترض معدل نمو وهمي 3.5% سنوياً
SIMULATED_ANNUAL_GROWTH_RATE = 0.035 

# --- إعدادات OSMnx ---
ox.settings.use_cache = True
ox.settings.log_console = False

# --- تهيئة حالة الجلسة ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# --- العنوان ---
st.title("🏙️ منصة راصد | رصد التمدد العمراني الذكي")
st.markdown("""
<style>
.big-font { font-size:20px !important; color: #4CAF50; }
</style>
<p class="big-font">نظام نمذجة جيومكاني لحساب مؤشرات التنمية المستدامة (11.3.1)</p>
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
    
    # تحديد نطاق متحرك
    base_year = st.slider("سنة الأساس (الماضي المحاكى)", 2010, 2020, 2015)
    target_year = st.slider("سنة الهدف (التحليل / الإسقاط)", LIVE_DATA_YEAR, 2035, 2030) # النطاق يصل الآن لـ 2035

    if target_year < LIVE_DATA_YEAR:
        st.warning(f"للتنبؤ، يجب أن تكون سنة الهدف أكبر من أو تساوي {LIVE_DATA_YEAR}.")

    st.write("---")
    def run_analysis():
        st.session_state.data_loaded = True
    
    st.button("🚀 تشغيل التحليل", on_click=run_analysis, type="primary")
    
    st.info(f"ملاحظة: البيانات الحية مفترضة لعام {LIVE_DATA_YEAR}. الأرقام المستقبلية هي إسقاطات إحصائية بسيطة.")

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
        
        with st.spinner('جاري بناء نماذج الإسقاط الزمني والمكاني...'):
            area, current_buildings_live, hist_buildings = process_analysis(coords["lat"], coords["lon"])
            
            if len(current_buildings_live) == 0:
                st.error("لا توجد بيانات كافية.")
            else:
                
                # 1. حسابات الاسقاط (Prediction Logic)
                built_curr_live_proj = current_buildings_live.to_crs(epsg=32638).geometry.area.sum()
                
                if target_year > LIVE_DATA_YEAR:
                    # حساب عدد السنوات الإضافية
                    extra_years = target_year - LIVE_DATA_YEAR
                    # حساب عامل النمو المركب (Compound Growth)
                    growth_factor = (1 + SIMULATED_ANNUAL_GROWTH_RATE) ** extra_years
                    
                    # إسقاط المساحة المبنية المستقبلية
                    built_target_proj = built_curr_live_proj * growth_factor
                    
                    # إسقاط عدد المباني (للأغراض العددية فقط)
                    len_target = int(len(current_buildings_live) * growth_factor)
                    
                    # المباني المستخدمة للعرض المرئي هي المباني الحالية (لأننا لا نرسم مبانٍ خيالية)
                    buildings_for_map = current_buildings_live
                    
                else: # إذا كان الهدف هو الحاضر أو الماضي القريب
                    built_target_proj = built_curr_live_proj
                    len_target = len(current_buildings_live)
                    buildings_for_map = current_buildings_live
                    
                # 2. حسابات الماضي
                area_proj = area.to_crs(epsg=32638)
                hist_proj = hist_buildings.to_crs(epsg=32638)
                
                total_area_km2 = area_proj.geometry.area.sum() / 1e6
                built_hist_proj = hist_proj.geometry.area.sum()
                
                # 3. حساب معدل التمدد الكلي (من سنة الأساس للهدف)
                sprawl_rate = 0
                if built_hist_proj > 0:
                    sprawl_rate = ((built_target_proj - built_hist_proj) / built_hist_proj) * 100
                
                # 4. عرض المؤشرات (KPIs)
                st.subheader(f"📊 لوحة مؤشرات النمو الحضري: {selected_area}")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("النطاق (كم²)", f"{total_area_km2:.2f}")
                col2.metric(f"المساحة المبنية ({base_year})", f"{built_hist_proj/1e6:.2f} مليون م²")
                col3.metric(f"المساحة المتوقعة ({target_year})", f"{built_target_proj/1e6:.2f} مليون م²")
                col4.metric(f"معدل التمدد ({base_year} - {target_year})", f"{sprawl_rate:.1f}%", help="يُحسب بناءً على معدل نمو سنوي 3.5% بعد 2025.")
                
                # 5. الرسوم البيانية
                st.write("---")
                st.subheader("📈 تحليل النمو الزمني (Projection vs. Reality)")
                chart_data = {
                    'السنة': [base_year, LIVE_DATA_YEAR, target_year],
                    'المساحة المبنية': [built_hist_proj, built_curr_live_proj, built_target_proj]
                }
                
                # إظهار الإسقاط كأنه يكمل المنحنى
                st.bar_chart(chart_data, x='السنة', y='المساحة المبنية', color="#FF4B4B")
                
                # 6. الخريطة التفاعلية (للعرض المرئي فقط، لا يمكننا رسم مبانٍ غير موجودة)
                st.write("---")
                st.subheader("🗺️ خريطة التغير المكاني (بصمة التمدد)")
                
                m = folium.Map(location=[coords["lat"], coords["lon"]], zoom_start=15, tiles="CartoDB positron")
                
                # طبقة التمدد (أحمر)
                folium.GeoJson(
                    buildings_for_map,
                    name=f'Urban Fabric {LIVE_DATA_YEAR}',
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
                
                st.success(f"✅ تم تحليل البيانات وإسقاط النمو حتى عام {target_year}.")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
else:
    st.info("👈 اختر المنطقة واضغط 'تشغيل التحليل'.")
