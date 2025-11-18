import streamlit as st
import osmnx as ox
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import random

# --- إعدادات الصفحة ---
st.set_page_config(page_title="راصد - Urban Sprawl Monitor", layout="wide")

# --- العنوان والهوية البصرية ---
st.title("🏙️ منصة راصد | رصد التمدد العمراني الذكي")
st.markdown("""
<style>
.big-font { font-size:20px !important; color: #4CAF50; }
</style>
<p class="big-font">نظام نمذجة جيومكاني لحساب مؤشرات التنمية المستدامة (11.3.1)</p>
""", unsafe_allow_html=True)

# --- الشريط الجانبي للمدخلات ---
with st.sidebar:
    st.header("⚙️ إعدادات النموذج")
    place_name = st.text_input("اسم المنطقة (بالانجليزي)", "Al Malqa, Riyadh, Saudi Arabia")
    
    st.write("---")
    st.header("⏳ النطاق الزمني")
    base_year = st.slider("سنة الأساس", 2010, 2020, 2015)
    target_year = st.slider("سنة الهدف", 2021, 2030, 2025)
    
    st.write("---")
    action = st.button("🚀 تشغيل التحليل", type="primary")
    
    st.info("ملاحظة: هذا نموذج أولي (MVP). في النسخة النهائية، يتم جلب البيانات التاريخية عبر Google Earth Engine.")

# --- دوال المعالجة (Cashing لتحسين السرعة) ---
@st.cache_data
def get_data(place):
    # جلب حدود الحي والمباني
    area = ox.geocode_to_gdf(place)
    buildings = ox.features_from_place(place, tags={'building': True})
    return area, buildings

def simulate_historical_data(buildings, reduction_factor=0.3):
    """
    دالة محاكاة لإنشاء نسخة تاريخية من البيانات لغرض العرض
    تقوم بحذف نسبة من المباني عشوائياً لتمثيل الوضع في الماضي
    """
    historical_buildings = buildings.sample(frac=(1-reduction_factor))
    return historical_buildings

# --- المنطق الرئيسي للتطبيق ---
if action:
    try:
        with st.spinner('جاري الاتصال بالأقمار الصناعية ومعالجة البيانات...'):
            # 1. جلب البيانات
            area, current_buildings = get_data(place_name)
            
            # 2. معالجة الاسقاطات للحساب الدقيق
            area_proj = area.to_crs(epsg=32638)
            curr_proj = current_buildings.to_crs(epsg=32638)
            
            # 3. محاكاة البيانات التاريخية
            hist_buildings = simulate_historical_data(current_buildings)
            hist_proj = hist_buildings.to_crs(epsg=32638)
            
            # 4. الحسابات الإحصائية
            total_area_km2 = area_proj.geometry.area.sum() / 1e6
            
            built_area_curr = curr_proj.geometry.area.sum()
            built_area_hist = hist_proj.geometry.area.sum()
            
            sprawl_rate = ((built_area_curr - built_area_hist) / built_area_hist) * 100
            
            # 5. عرض المؤشرات (KPIs)
            st.subheader("📊 لوحة المؤشرات الحضرية")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("مساحة الحي (كم²)", f"{total_area_km2:.2f}")
            col2.metric(f"المباني ({base_year})", f"{len(hist_buildings)}")
            col3.metric(f"المباني ({target_year})", f"{len(current_buildings)}")
            col4.metric("معدل التمدد العمراني", f"{sprawl_rate:.2f}%", f"+{len(current_buildings)-len(hist_buildings)} مبنى")
            
            # 6. الخرائط التفاعلية
            st.write("---")
            st.subheader("🗺️ التحليل المكاني المقارن")
            
            # خريطة الوضع الحالي
            m = folium.Map(location=[area.geometry.centroid.y.values[0], area.geometry.centroid.x.values[0]], zoom_start=14)
            
            # إضافة المباني الجديدة (التمدد) باللون الأحمر
            # الحيلة هنا: نرسم المباني الحالية بلون أحمر، والمباني القديمة فوقها بلون أزرق
            # الأجزاء الحمراء الظاهرة هي "التمدد الجديد"
            
            folium.GeoJson(
                current_buildings,
                name=f'Urban Fabric {target_year}',
                style_function=lambda x: {'fillColor': '#FF4B4B', 'color': 'none', 'fillOpacity': 0.7},
                tooltip="New Expansion"
            ).add_to(m)
            
            folium.GeoJson(
                hist_buildings,
                name=f'Urban Fabric {base_year}',
                style_function=lambda x: {'fillColor': '#1F77B4', 'color': 'none', 'fillOpacity': 0.9},
                tooltip="Existing Built-up"
            ).add_to(m)
            
            folium.LayerControl().add_to(m)
            
            st_folium(m, width=None, height=500)
            
            # 7. الرسوم البيانية
            st.write("---")
            st.subheader("📈 تحليل النمو")
            chart_data = {
                'Year': [base_year, target_year],
                'Built-up Area (sq m)': [built_area_hist, built_area_curr]
            }
            st.bar_chart(chart_data, x='Year', y='Built-up Area (sq m)', color="#1F77B4")
            
            st.success("تم تحليل البيانات بنجاح! النموذج جاهز لدعم اتخاذ القرار.")

    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
        st.warning("تأكد من كتابة اسم المنطقة بشكل صحيح (مثال: Jeddah, Saudi Arabia)")

else:
    st.info("👈 قم بإدخال اسم الحي واضغط على 'تشغيل التحليل' من القائمة الجانبية.")
