import streamlit as st
import osmnx as ox
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import box
import numpy as np
import pandas as pd

# --- ثوابت النمذجة (للتنبؤ المحاكي) ---
LIVE_DATA_YEAR = 2025
SIMULATED_URBAN_ANNUAL_GROWTH = 0.035
SIMULATED_POP_ANNUAL_GROWTH = 0.025 

# --- بيانات SDG الحقيقية لمنطقة "الرياض - الملقا" (مثال إدخال بيانات حقيقية) ---
# يجب تعديل هذه الأرقام بناءً على استخلاصك الحقيقي من WorldPop/GEE
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

# --- إعدادات OSMnx / الحالة / العنوان (لا تتغير) ---
# ... (الكود من البداية حتى بداية الشريط الجانبي يبقى كما هو) ...

# --- الشريط الجانبي ---
# ... (استبدل هذا الجزء داخل الشريط الجانبي)
with st.sidebar:
    st.header("⚙️ إعدادات النموذج")
    selected_area = st.selectbox("اختر المنطقة للدراسة:", list(LOCATIONS.keys()))
    
    st.write("---")
    st.header("⏳ النطاق الزمني")
    
    # تحديد سنوات التحليل بناءً على البيانات الحقيقية المدخلة
    if selected_area in REAL_SDG_DATA:
        base_year_fixed = REAL_SDG_DATA[selected_area]["base_year_data"]
        current_year_fixed = REAL_SDG_DATA[selected_area]["current_year_data"]
        
        st.caption(f"التحليل يجري بناءً على الفترة الحقيقية: {base_year_fixed} - {current_year_fixed}")
        
        # السماح بالإسقاط المستقبلي بعد السنة الحالية
        target_year = st.slider("سنة الهدف (الإسقاط)", current_year_fixed, 2035, 2030)
    else:
        # باقي المناطق تستخدم المحاكاة العامة
        base_year_fixed = st.slider("سنة الأساس (الماضي المحاكى)", 2010, 2020, 2015)
        target_year = st.slider("سنة الهدف (الإسقاط)", LIVE_DATA_YEAR, 2035, 2030)
        current_year_fixed = LIVE_DATA_YEAR

    st.write("---")
    def run_analysis():
        st.session_state.data_loaded = True
    
    st.button("🚀 تشغيل التحليل", on_click=run_analysis, type="primary")
    
    st.info("ملاحظة: البيانات الحية للملقا (2015-2020) تم تحميلها مسبقاً من WorldPop/GEE.")
# ... (نهاية الشريط الجانبي)


# --- المنطق الرئيسي للتطبيق (التعديلات هنا) ---
if st.session_state.data_loaded:
    try:
        coords = LOCATIONS[selected_area]
        
        with st.spinner('جاري حساب مؤشر SDG 11.3.1 بالبيانات الحقيقية...'):
            area, current_buildings_live, hist_buildings = process_analysis(coords["lat"], coords["lon"])
            
            # ** المنطق الجديد: قراءة البيانات الحقيقية أو المحاكاة **
            if selected_area in REAL_SDG_DATA:
                data = REAL_SDG_DATA[selected_area]
                Urb_hist = data["Urb_hist_area"]
                Urb_curr = data["Urb_current_area"]
                Pop_hist = data["Pop_hist"]
                Pop_curr = data["Pop_current"]
                time_span_base = data["current_year_data"] - data["base_year_data"]

                # تطبيق الإسقاط المستقبلي على البيانات الحقيقية
                if target_year > data["current_year_data"]:
                    extra_years = target_year - data["current_year_data"]
                    growth_factor_urb = (1 + SIMULATED_URBAN_ANNUAL_GROWTH) ** extra_years
                    growth_factor_pop = (1 + SIMULATED_POP_ANNUAL_GROWTH) ** extra_years
                    
                    Urb_target = Urb_curr * growth_factor_urb
                    Pop_target = Pop_curr * growth_factor_pop
                    
                    # حساب الفترة الزمنية للمؤشر (من سنة الأساس الحقيقية للهدف المستقبلي)
                    time_span = target_year - data["base_year_data"]
                else:
                    Urb_target = Urb_curr
                    Pop_target = Pop_curr
                    time_span = data["current_year_data"] - data["base_year_data"] # (فقط للفترة الحقيقية)

                st.success(f"✅ تم استخدام بيانات حقيقية لمنطقة {selected_area} للفترة {data['base_year_data']} - {data['current_year_data']} مع إسقاط مستقبلي حتى {target_year}.")
            
            else:
                # منطق المحاكاة العامة لباقي المناطق (يبقى كما كان)
                # ... (هنا يتم وضع منطق المحاكاة القديم ل Urb_target و Pop_target) ...
                st.warning("⚠️ هذه المنطقة تستخدم بيانات محاكاة. اختر 'الرياض - حي الملقا' للبيانات الحقيقية.")
                return

            
            # ** 3. حساب المؤشرات (SDG 11.3.1 - LCRPGR) - يستخدم الآن الأرقام الحقيقية **
            
            LCR = np.log(Urb_target / Urb_hist) / time_span if Urb_hist > 0 else 0
            PGR = np.log(Pop_target / Pop_hist) / time_span if Pop_hist > 0 else 0
            
            LCRPGR = LCR / PGR if PGR > 0 else 0

            # 4. عرض المؤشرات (KPIs)
            # ... (باقي كود عرض KPI يبقى كما هو لكن بـ Urb_target و Pop_target) ...
            
            # 5. عرض الرسوم البيانية
            # ... (باقي كود الرسم البياني يبقى كما هو) ...

            # 6. الخريطة (للعرض المرئي)
            # ... (باقي كود الخريطة يبقى كما هو) ...


    except Exception as e:
        st.error(f"حدث خطأ: {e}")
