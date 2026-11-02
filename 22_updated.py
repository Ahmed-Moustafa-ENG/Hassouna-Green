import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
import streamlit as st
import datetime
import calendar
import base64
import html
import io
import json
import os
import requests
import time
import warnings
warnings.filterwarnings('ignore')
import math
import re
import llm_layer
import hassouna_db
import ml_judge
try:
    from PIL import Image
except Exception:
    Image = None

# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — TRANSLATIONS (ثنائي اللغة الكامل)
# ═══════════════════════════════════════════════════════════════════════════════

TRANSLATIONS = {
    "ar": {
        "project_name": "حسونة جرين",
        "project_sub": "منصة ذكية لتخطيط الأراضي والزراعة المستدامة وترشيد المياه",
        "brand_badge": "Hassouna Green",
        "creators_label": "إعداد وتطوير",
        "creators_and": "و",
        "creator_1": "أحمد مصطفى",
        "creator_2": "عبد الرحمن خالد",
        "fig_swipe_hint": "اسحب يمينًا ويسارًا لرؤية الرسم كاملًا",
        "app_title": "حسونة جرين — تخطيط الأراضي المستدام",
        "app_subtitle": "توصيات زراعية ومائية مبنية على بيانات الموقع",
        "step_location": "الموقع والتاريخ",
        "step_land": "بيانات الأرض",
        "step_water": "الري والمياه",
        "step_result": "النتائج",
        "next": "التالي ←",
        "prev": "→ السابق",
        "generate": "🚀 توليد التصميم",
        "settings": "إعدادات الموقع",
        "governorate": "المحافظة",
        "region": "المنطقة / الحي",
        "date_label": "تاريخ التصميم",
        "day": "اليوم", "month": "الشهر", "year": "السنة",
        "soil": "نوع التربة",
        "area_unit": "وحدة المساحة",
        "width": "العرض (م)", "height": "الطول (م)",
        "water_budget": "ميزانية الري",
        "water_low": "🌵 منخفض جداً",
        "water_mid": "🌿 متوسط",
        "water_high": "🌊 عالٍ",
        "how_works": "كيف يعمل النظام؟",
        "step1": "اختر المحافظة والمنطقة — التربة تُحدَّد تلقائياً",
        "step2": "اختر التاريخ — الفصل ودرجة الحرارة تُحدَّد تلقائياً",
        "step3": "يحلل النظام قاعدة نباتات منسقة لاقتراح الأنسب للموقع",
        "step4": "يعرض النظام درجة قاعدية شفافة، مع مراجعة لغوية اختيارية بالذكاء الاصطناعي",
        "step5": "يرسم مخطط التوزيع ويحسب توفير المياه",
        "step6": "أعطِ تقييمك وساعد النظام على التحسين",
        "analysis_success": "✅ تم تحليل موقعك بنجاح",
        "weekly_consumption": "💧 احتياج الري الأسبوعي التقديري",
        "traditional": "خط أساس مرجعي عالي الاستهلاك",
        "water_saving": "✅ توفير المياه",
        "saving_label": "توفير في المياه",
        "recommended_plants": "🌱 النباتات الموصى بها",
        "layout_title": "🗺️ مخطط التوزيع المقترح",
        "chart_title": "📊 مقارنة الاستهلاك المائي",
        "judge_title": "التقييم القاعدي للموقع",
        "summary_title": "📋 الملخص الشامل",
        "feedback_title": "💬 تقييمك يُحسّن النظام",
        "feedback_q": "كيف تقيّم جودة التصميم المقترح؟",
        "feedback_comment": "تعليق إضافي (اختياري)",
        "feedback_submit": "إرسال التقييم",
        "feedback_thanks": "شكراً! تقييمك سيُحسّن النموذج 🌱",
        "location_data": "بيانات الموقع",
        "water_analysis": "تحليل الاستهلاك المائي",
        "scientific_rec": "إرشادات تخطيطية",
        "season_label": "الفصل",
        "temp_label": "درجة الحرارة",
        "soil_label": "نوع التربة",
        "area_label": "المساحة",
        "best_planting": "أفضل وقت للزراعة",
        "best_watering": "أنسب وقت للري",
        "soil_improvement": "تحسين التربة",
        "env_impact": "الأثر البيئي",
        "season_suitability": "ملاءمة الفصل",
        "weekly": "أسبوعي", "monthly": "شهري", "yearly": "سنوي",
        "traditional_label": "خط أساس Kc=0.85", "our_system": "ET₀ × Kc تقديري",
        "liters": "لتر", "meters": "م²", "km": "كم²",
        "path": "ممر رئيسي",
        "water_icons": {1: "💧", 2: "💧💧", 3: "💧💧💧"},
        "months": {
            1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
            7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
        },
        "seasons": {
            "winter": ("🌨️ فصل الشتاء", "بارد"),
            "spring": ("🌸 فصل الربيع", "معتدل"),
            "summer": ("☀️ فصل الصيف", "حار"),
            "autumn": ("🍂 فصل الخريف", "معتدل دافئ"),
        },
        "judge_excellent": "ممتاز — تصميم مثالي للموقع",
        "judge_good": "جيد جداً — توافق عالٍ مع الظروف البيئية",
        "judge_avg": "مقبول — يُنصح بمراجعة بعض الاختيارات",
        "judge_criteria": "معايير التقييم",
        "judge_water_eff": "كفاءة استخدام المياه",
        "judge_climate": "توافق المناخ",
        "judge_soil": "ملاءمة التربة",
        "judge_diversity": "تنوع النباتات",
        "judge_beauty": "القيمة الجمالية",
        "feedback_options": ["⭐ ضعيف","⭐⭐ مقبول","⭐⭐⭐ جيد","⭐⭐⭐⭐ جيد جداً","⭐⭐⭐⭐⭐ ممتاز"],
        "plants_count": "عدد النباتات",
        "design_date": "تاريخ التصميم",
        "region_label": "المنطقة",
        "gov_label": "المحافظة",
        "intro_loading": "جارٍ تحميل النظام...",
        "intro_skip": "تخطي المقدمة",
        "start_design": "ابدأ التصميم",
        "form_title_1": "📍 الخطوة 1 — الموقع والتاريخ",
        "form_title_2": "🪨 الخطوة 2 — بيانات الأرض",
        "form_title_3": "💧 الخطوة 3 — الري والمياه",
        "form_progress": "التقدم",
        "live_temp": "درجة حرارة مباشرة",
        "est_temp": "درجة حرارة تقديرية",
        "soil_note": "تم اكتشاف التربة تلقائياً من موقعك",
        "area_total": "إجمالي المساحة",
        "plant_filter": "فلتر النباتات",
        "all_types": "جميع الأنواع",
        "stats_title": "إحصائيات النظام",
        "total_plants_db": "نباتات في قاعدة البيانات",
        "mapped_locations_count": "مواقع ومناطق مدرجة",
        "soil_types_count": "نوع تربة",
        "scoring_method": "منهج التقييم",
    },
    "en": {
        "project_name": "Hassouna Green",
        "project_sub": "A smart platform for sustainable land and planting plans",
        "brand_badge": "Hassouna Green",
        "creators_label": "Created by",
        "creators_and": "&",
        "creator_1": "Ahmed Moustafa",
        "creator_2": "Abdelrahman Khaled",
        "fig_swipe_hint": "Swipe sideways to see the whole figure",
        "app_title": "Hassouna Green — Sustainable Land Planning",
        "app_subtitle": "Climate-aware planting and irrigation planning",
        "step_location": "Location & Date",
        "step_land": "Land Data",
        "step_water": "Irrigation",
        "step_result": "Results",
        "next": "Next →",
        "prev": "← Back",
        "generate": "🚀 Generate Design",
        "settings": "Site Settings",
        "governorate": "Governorate",
        "region": "District / Area",
        "date_label": "Design Date",
        "day": "Day", "month": "Month", "year": "Year",
        "soil": "Soil Type",
        "area_unit": "Area Unit",
        "width": "Width (m)", "height": "Length (m)",
        "water_budget": "Irrigation Budget",
        "water_low": "🌵 Very Low",
        "water_mid": "🌿 Medium",
        "water_high": "🌊 High",
        "how_works": "How does the system work?",
        "step1": "Choose governorate & district — soil is auto-detected",
        "step2": "Choose date — season & temperature auto-detected",
        "step3": "The system filters a curated plant catalog for site suitability",
        "step4": "Shows a transparent rule-based score, with optional generative-AI review",
        "step5": "Generates layout map and calculates water savings",
        "step6": "Give your feedback to help the system improve",
        "analysis_success": "✅ Site analysis complete",
        "weekly_consumption": "💧 Estimated Weekly Irrigation",
        "traditional": "High-water comparison baseline",
        "water_saving": "✅ Water Saving",
        "saving_label": "Water Savings",
        "recommended_plants": "🌱 Recommended Plants",
        "layout_title": "🗺️ Proposed Layout",
        "chart_title": "📊 Water Consumption Comparison",
        "judge_title": "Rule-based Site Score",
        "summary_title": "📋 Full Summary",
        "feedback_title": "💬 Your Feedback Improves the System",
        "feedback_q": "How do you rate the proposed design?",
        "feedback_comment": "Additional comment (optional)",
        "feedback_submit": "Submit Feedback",
        "feedback_thanks": "Thank you! Your feedback will improve the model 🌱",
        "location_data": "Location Data",
        "water_analysis": "Water Consumption Analysis",
        "scientific_rec": "Planning Guidance",
        "season_label": "Season",
        "temp_label": "Temperature",
        "soil_label": "Soil Type",
        "area_label": "Area",
        "best_planting": "Best Planting Time",
        "best_watering": "Best Watering Time",
        "soil_improvement": "Soil Improvement",
        "env_impact": "Environmental Impact",
        "season_suitability": "Season Suitability",
        "weekly": "Weekly", "monthly": "Monthly", "yearly": "Annually",
        "traditional_label": "Baseline Kc=0.85", "our_system": "ET₀ × estimated Kc",
        "liters": "L", "meters": "m²", "km": "km²",
        "path": "Main Path",
        "water_icons": {1: "💧", 2: "💧💧", 3: "💧💧💧"},
        "months": {
            1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
            7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"
        },
        "seasons": {
            "winter": ("🌨️ Winter", "Cold"),
            "spring": ("🌸 Spring", "Mild"),
            "summer": ("☀️ Summer", "Hot"),
            "autumn": ("🍂 Autumn", "Warm"),
        },
        "judge_excellent": "Excellent — Ideal design for this site",
        "judge_good": "Very Good — High compatibility with environmental conditions",
        "judge_avg": "Acceptable — Some selections may need revision",
        "judge_criteria": "Evaluation Criteria",
        "judge_water_eff": "Water Use Efficiency",
        "judge_climate": "Climate Compatibility",
        "judge_soil": "Soil Suitability",
        "judge_diversity": "Plant Diversity",
        "judge_beauty": "Aesthetic Value",
        "feedback_options": ["⭐ Poor","⭐⭐ Fair","⭐⭐⭐ Good","⭐⭐⭐⭐ Very Good","⭐⭐⭐⭐⭐ Excellent"],
        "plants_count": "Plants Count",
        "design_date": "Design Date",
        "region_label": "District",
        "gov_label": "Governorate",
        "intro_loading": "Loading system...",
        "intro_skip": "Skip Intro",
        "start_design": "Start Design",
        "form_title_1": "📍 Step 1 — Location & Date",
        "form_title_2": "🪨 Step 2 — Land Data",
        "form_title_3": "💧 Step 3 — Irrigation",
        "form_progress": "Progress",
        "live_temp": "Live temperature",
        "est_temp": "Estimated temperature",
        "soil_note": "Soil auto-detected from your location",
        "area_total": "Total Area",
        "plant_filter": "Plant Filter",
        "all_types": "All Types",
        "stats_title": "System Stats",
        "total_plants_db": "Plants in Database",
        "mapped_locations_count": "Mapped regions and locations",
        "soil_types_count": "Soil Types",
        "scoring_method": "Scoring method",
    }
}
# PART 2 — REFERENCE DATA (SQLite database: hassouna_green.db)
# Countries, locations, monthly temperature normals, regions, soil types, soil
# compatibility, the plant catalog and provisional planning Kc values are stored
# in hassouna_green.db (see hassouna_db.py). Edit the database, not this file.
# The cache key includes the database file's modification time and size, so a
# saved database edit is picked up on the next app rerun.
@st.cache_data(show_spinner=False)
def _load_reference_data(db_signature):
    return hassouna_db.load_reference_data(db_signature[0])

try:
    _REFERENCE_DATA = _load_reference_data(hassouna_db.database_signature())
except hassouna_db.DatabaseError as _db_error:
    st.error("تعذر تحميل قاعدة البيانات / The database could not be loaded:\n\n" + str(_db_error))
    st.stop()
GOVERNORATE_DATA = _REFERENCE_DATA["locations"]
COUNTRY_LOCATION_KEYS = _REFERENCE_DATA["country_location_keys"]
GULF_AI_COUNTRIES = _REFERENCE_DATA["countries"]
COUNTRY_LABELS_EN = _REFERENCE_DATA["country_labels_en"]
ALL_SOIL_TYPES = _REFERENCE_DATA["soil_types"]
SOIL_COMPAT = _REFERENCE_DATA["soil_compatibility"]
LANDSCAPE_KC_BY_USE = _REFERENCE_DATA["use_kc"]
SOIL_LABELS_EN = _REFERENCE_DATA["soil_labels_en"]
USE_LABELS_EN = _REFERENCE_DATA["use_labels_en"]
SOIL_TRAITS = _REFERENCE_DATA["soil_traits"]


# Display labels. Arabic names are the internal keys; English comes from the database.
def label_country(country, lang):
    return COUNTRY_LABELS_EN.get(country, country) if lang == "en" else country


def label_location(location, lang):
    if lang != "en":
        return location
    return GOVERNORATE_DATA.get(location, {}).get("name_en", location)


def label_region(location, region, lang):
    if lang != "en":
        return region
    return GOVERNORATE_DATA.get(location, {}).get("region_names_en", {}).get(region, region)


def label_soil(soil, lang):
    return SOIL_LABELS_EN.get(soil, soil) if lang == "en" else soil


def label_use(use, lang):
    return USE_LABELS_EN.get(use, use) if lang == "en" else use

def get_plants_database():
    """Return a copy of the plant catalog loaded from hassouna_green.db."""
    return _REFERENCE_DATA["plants"].copy()

# PART 3b — MACHINE-LEARNING + DEEP-LEARNING JUDGE (ml_judge.py; weights in ml/)
# Trained offline by ml/train_ml_judge.py on real plant observations and
# WorldClim climate. The cache key changes when the model files are replaced.
ML_FEATURE_LABELS = {
    "bio1": ("متوسط الحرارة السنوي", "annual mean temperature"),
    "bio4": ("التباين الموسمي للحرارة", "temperature seasonality"),
    "bio5": ("أعلى حرارة في أدفأ شهر", "warmest-month maximum"),
    "bio6": ("أدنى حرارة في أبرد شهر", "coldest-month minimum"),
    "bio12": ("الأمطار السنوية", "annual rainfall"),
    "bio15": ("موسمية الأمطار", "rainfall seasonality"),
    "bio17": ("أمطار أجف ربع سنة", "driest-quarter rainfall"),
}


def _ml_source_label(data, lang):
    if data.get("source") == "gbif":
        return _label(lang, "سجلات GBIF", "GBIF occurrence records")
    if "cultivated" in data.get("record_kinds", []):
        return _label(lang, "مشاهدات iNaturalist لنباتات برية (درجة بحثية) ومزروعة (بتعريف متفق عليه)",
                      "iNaturalist observations of wild (research-grade) and planted (agreed identification) plants")
    return _label(lang, "مشاهدات iNaturalist بدرجة بحثية", "iNaturalist research-grade observations")


def _ml_judge_signature():
    sig = []
    for name in (ml_judge.MODEL_FILE, ml_judge.CARD_FILE):
        try:
            stat = (ml_judge.MODEL_DIR / name).stat()
            sig.append((name, stat.st_mtime_ns, stat.st_size))
        except FileNotFoundError:
            sig.append((name, None, None))
    return tuple(sig)


@st.cache_resource(show_spinner=False)
def _load_ml_judge(signature):
    return ml_judge.MLJudge.load()


def _warming_label(lang, w):
    return _label(lang, "المناخ الحالي", "Today's climate") if w == 0 else f"+{w:.0f} °C"


def render_ml_judge(lang, governorate, recommended):
    """Show the climate-match judge. Returns its result dict, or None if unavailable."""
    st.markdown("### 🤖 " + _label(lang, "حَكَم تعلّم الآلة والتعلّم العميق", "Machine-learning & deep-learning judge"))
    judge = _load_ml_judge(_ml_judge_signature())
    if judge is None:
        st.info(_label(lang,
            "ملفات النموذج غير موجودة. ضع المجلد ml (وفيه ml_judge_model.npz و ml_judge_card.json) بجوار التطبيق.",
            "Model files not found. Put the ml folder (with ml_judge_model.npz and ml_judge_card.json) next to the app."))
        return None
    climate = GOVERNORATE_DATA.get(governorate, {}).get("climate")
    if not climate:
        st.info(_label(lang, "لا توجد بيانات مناخية لهذا الموقع في قاعدة البيانات.",
                       "This location has no climate record in the database."))
        return None

    ev, data, arch = judge.metrics(), judge.data_summary(), judge.card.get("architecture", {})
    src = _ml_source_label(data, lang)
    uses_rain = any(f in judge.feature_names for f in ("bio12", "bio15", "bio17"))
    feature_text = ("، " if lang == "ar" else ", ").join(
        ML_FEATURE_LABELS.get(f, (f, f))[0 if lang == "ar" else 1] for f in judge.feature_names)
    auc = {k: ev[k]["mean_auc"] for k in ("logistic_regression", "deep_neural_network", "ensemble")}
    st.caption(_label(lang,
        f"تدرّب على {data['records_used']:,} مشاهدة حقيقية لـ {data['taxa_modeled']} نوعاً وجنساً نباتياً ({src}) "
        f"مع بيانات المناخ WorldClim، واختُبر على مناطق من العالم لم يرها أثناء التدريب: "
        f"الانحدار اللوجستي AUC {auc['logistic_regression']:.2f}، الشبكة العصبية العميقة AUC {auc['deep_neural_network']:.2f}، "
        f"والنموذجان معاً AUC {auc['ensemble']:.2f} (0.5 = تخمين عشوائي، 1.0 = مثالي). "
        + ("يقيّم المناخ فقط؛ التربة والمياه يقيّمها التقييم القاعدي أعلاه." if uses_rain else
           "يقيّم تحمّل الحرارة والبرودة فقط؛ استُبعدت الأمطار لأن الري يحل محلها، والتربة والمياه يقيّمها التقييم القاعدي وحساب المياه أعلاه."),
        f"Trained on {data['records_used']:,} real observations of {data['taxa_modeled']} plant species and genera ({src}) "
        f"with WorldClim climate data, and tested on world regions it never saw in training: "
        f"logistic regression AUC {auc['logistic_regression']:.2f}, deep neural network AUC {auc['deep_neural_network']:.2f}, "
        f"both combined AUC {auc['ensemble']:.2f} (0.5 = random guessing, 1.0 = perfect). "
        + ("It judges climate only; soil and water are covered by the rule-based score above." if uses_rain else
           "It judges heat and cold tolerance only; rainfall is left out because irrigation replaces rain, and soil "
           "and water are covered by the rule-based score and water engine above.")))

    warming = st.select_slider(
        _label(lang, "🌡️ اختبار الإجهاد المناخي (احترار منتظم)", "🌡️ Climate stress test (uniform warming)"),
        options=[0.0, 1.0, 2.0, 3.0], value=0.0, format_func=lambda w: _warming_label(lang, w), key="ml_warming")

    plants = [{"name": r["name"], "scientific_name": r.get("scientific_name", ""), "taxon_key": r.get("taxon_key")}
              for _, r in recommended.iterrows()]
    display = {r["name"]: (r["name"] if lang == "ar" else r["name_en"]) for _, r in recommended.iterrows()}
    res = judge.judge(plants, climate, warming)
    if res["score"] is None:
        st.info(_label(lang, "لا يملك النموذج سجلات كافية لأي من النباتات الموصى بها لتقييمها.",
                       "None of the recommended plants has enough real-world records for the model to judge."))
        return res
    today = res if warming == 0 else judge.judge(plants, climate, 0.0)

    c1, c2, c3 = st.columns(3)
    c1.metric(_label(lang, "درجة التوافق المناخي", "ML climate-match score"), f"{res['score']:.0f}/100",
              delta=None if warming == 0 else f"{res['score'] - today['score']:+.0f}")
    c2.metric(_label(lang, "داخل النطاق المناخي المعروف", "Within known climate range"),
              f"{res['n_within']}/{res['n_modeled']}")
    c3.metric(_label(lang, "غير مُقيَّمة بالنموذج", "Not judged by the model"), f"{res['n_total'] - res['n_modeled']}")

    def pct(v):
        return "—" if v is None else f"{v:.0f}%"

    def verdict(r):
        if not r["modeled"]:
            return "— " + _label(lang, "غير مُقيَّم (اسم عام أو سجلات قليلة)", "Not judged (generic name or too few records)")
        if r["within_range"]:
            return "✅ " + _label(lang, "داخل النطاق المعروف", "Within known range")
        return "⚠️ " + _label(lang, "خارج النطاق المعروف", "Outside known range")

    table = pd.DataFrame([{
        _label(lang, "النبات", "Plant"): display.get(r["name"], r["name"]),
        _label(lang, "الاسم العلمي", "Scientific name"): r["scientific_name"] or "—",
        _label(lang, "انحدار لوجستي (تعلم آلي)", "Logistic regression (ML)"): pct(r.get("glm_pct")),
        _label(lang, "شبكة عصبية (تعلم عميق)", "Neural network (DL)"): pct(r.get("dnn_pct")),
        _label(lang, "التوافق المناخي المجمّع", "Combined climate match"): pct(r.get("match_pct")),
        _label(lang, "الحكم", "Verdict"): verdict(r),
    } for r in res["rows"]])
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption(_label(lang,
        "التوافق المناخي = ترتيب مناخ هذا الموقع بين الأماكن التي سُجّل فيها النبات فعلاً: 50% يعني أنه نموذجي مثل "
        "منتصف أماكنه المعروفة، وأقل من 10% يعني أنه خارج نطاقه المناخي المعروف. درجة النبات: 60 = حافة نطاقه المعروف، "
        "100 = نموذجي مثل منتصف أماكنه؛ ودرجة التصميم متوسط درجات النباتات. النبات خارج نطاقه قد يُزرع مع ري وعناية أكثر.",
        "Climate match = where this site's climate ranks among the places the plant is actually recorded: 50% means as "
        "typical as its median known location; below 10% means outside its known climate range. Plant score: 60 = edge "
        "of its known range, 100 = as typical as its median location; the design score is the average. A plant outside "
        "its range may still be grown with extra irrigation and care."))

    with st.expander(_label(lang, "📈 اختبار الاحترار: +1 / +2 / +3 °م", "📈 Warming stress test: +1 / +2 / +3 °C")):
        steps = judge.stress_test(plants, climate)
        sep = "، " if lang == "ar" else ", "
        st.dataframe(pd.DataFrame([{
            _label(lang, "السيناريو", "Scenario"): _warming_label(lang, s_["warming"]),
            _label(lang, "الدرجة", "Score"): f"{s_['score']:.0f}/100",
            _label(lang, "داخل النطاق", "Within range"): f"{s_['n_within']}/{s_['n_modeled']}",
            _label(lang, "نباتات خارج النطاق", "Plants outside range"):
                sep.join(display.get(n, n) for n in s_["dropped"]) or "—",
        } for s_ in steps]), hide_index=True, width="stretch")
        st.caption(_label(lang,
            "يضيف الاحترار المنتظم نفس عدد الدرجات إلى متوسط الحرارة السنوي وحرارة أدفأ وأبرد شهر. "
            "هذا اختبار حساسية وليس توقعاً مناخياً.",
            "Uniform warming adds the same number of degrees to the annual mean, warmest-month and coldest-month "
            "temperatures. It is a sensitivity test, not a climate projection."))

    with st.expander(_label(lang, "🔬 كيف تدرّب هذا الحكم وكيف اختُبر", "🔬 How this judge was trained and tested")):
        hidden = " → ".join(str(h) for h in arch.get("dnn_hidden", []))
        st.markdown(_label(lang,
            f"- **البيانات:** {data['records_used']:,} مشاهدة ({src}) منذ {data.get('min_year', 1950)}، في "
            f"{data['grid_cells']:,} خلية مناخية (~18 كم)، لـ {data['taxa_modeled']} نوعاً وجنساً لديها {data.get('min_cells', 20)} خلية على الأقل.\n"
            f"- **المناخ:** {len(judge.feature_names)} متغيرات من WorldClim 2.1 (1970-2000): {feature_text}.\n"
            f"- **تعلم آلي:** انحدار لوجستي لكل نبات على {arch.get('glm_terms', 14)} حداً (المتغيرات ومربعاتها).\n"
            f"- **تعلم عميق:** شبكة عصبية متعددة المخرجات {len(judge.feature_names)} → {hidden} → {arch.get('dnn_outputs', '')} "
            f"({arch.get('dnn_parameters', 0):,} معامل) مدرّبة بـ PyTorch.\n"
            "- **الاختبار:** تحقق متقاطع مكاني بخمس طيّات: قُسّم العالم إلى مربعات 5°×5° ويُقيَّم كل مربع بنموذج لم يتدرّب عليه.",
            f"- **Data:** {data['records_used']:,} observations ({src}) since {data.get('min_year', 1950)}, in "
            f"{data['grid_cells']:,} climate cells (~18 km), for {data['taxa_modeled']} species and genera with at least {data.get('min_cells', 20)} cells.\n"
            f"- **Climate:** {len(judge.feature_names)} WorldClim 2.1 variables (1970-2000): {feature_text}.\n"
            f"- **Machine learning:** one logistic regression per plant on {arch.get('glm_terms', 14)} terms (the variables and their squares).\n"
            f"- **Deep learning:** multi-output neural network {len(judge.feature_names)} → {hidden} → {arch.get('dnn_outputs', '')} "
            f"({arch.get('dnn_parameters', 0):,} parameters) trained with PyTorch.\n"
            "- **Test:** 5-fold spatial cross-validation: the world is split into 5°×5° blocks and every block is scored by a model that never trained on it."))
        names = {
            "logistic_regression": _label(lang, "انحدار لوجستي (تعلم آلي)", "Logistic regression (ML)"),
            "deep_neural_network": _label(lang, "شبكة عصبية عميقة (تعلم عميق)", "Deep neural network (DL)"),
            "ensemble": _label(lang, "النموذجان معاً", "Both combined"),
            "catalog_temperature_rule": _label(lang, "نطاقات الحرارة في كتالوج التطبيق (مرجع)", "App catalog temperature ranges (baseline)"),
        }
        st.dataframe(pd.DataFrame([{
            _label(lang, "الطريقة", "Method"): label,
            _label(lang, "متوسط AUC", "Mean AUC"): f"{ev[k]['mean_auc']:.3f}",
            _label(lang, "وسيط AUC", "Median AUC"): f"{ev[k]['median_auc']:.3f}",
            _label(lang, "نباتات AUC ≥ 0.7", "Plants with AUC ≥ 0.7"): f"{ev[k]['share_above_0_7'] * 100:.0f}%",
            _label(lang, "عدد النباتات", "Plants tested"): ev[k]["n_taxa"],
        } for k, label in names.items() if k in ev]), hide_index=True, width="stretch")
        st.markdown("**" + _label(lang, "حدود النموذج", "Limitations") + "**\n" + "\n".join(
            "- " + (item.get("ar") if lang == "ar" else item.get("en"))
            for item in judge.card.get("limitations", []) if isinstance(item, dict)))
    return res


# PART 4 — SEASON & CLIMATE LOGIC
def get_season(month, lang="ar"):
    T = TRANSLATIONS[lang]
    if month in [12, 1, 2]:   key = "winter"
    elif month in [3, 4, 5]:  key = "spring"
    elif month in [6, 7, 8]:  key = "summer"
    else:                      key = "autumn"
    return T["seasons"][key]
def get_temp(gov, month):
    return GOVERNORATE_DATA[gov]["monthly_temp"][month - 1]
@st.cache_data(ttl=900, show_spinner=False)
def fetch_live_weather(gov):
    """Return the current temperature when available; cached for 15 minutes."""
    data = GOVERNORATE_DATA.get(gov, {})
    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        return None
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m", "timezone": "auto"},
            timeout=8,
        )
        r.raise_for_status()
        current = r.json().get("current", {}).get("temperature_2m")
        return round(float(current), 1) if current is not None else None
    except Exception:
        return None


@st.cache_data(ttl=21600, show_spinner=False)
def _open_meteo_daily(endpoint, lat, lon, start_date, end_date):
    """Fetch daily Open-Meteo data; results are cached for six hours."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "et0_fao_evapotranspiration,temperature_2m_mean",
        "timezone": "auto",
    }
    if endpoint.endswith("/v1/forecast"):
        params["forecast_days"] = 16
    r = requests.get(endpoint, params=params, timeout=12)
    r.raise_for_status()
    return r.json().get("daily", {})


@st.cache_data(ttl=900, show_spinner=False)
def _monthly_et0_climatology(gov):
    """Return monthly mean daily ET0 from the five most recent complete years."""
    loc = GOVERNORATE_DATA.get(gov, {})
    lat, lon = loc.get("lat"), loc.get("lon")
    if lat is None or lon is None:
        return {}
    end_year = datetime.date.today().year - 1
    start_year = max(1940, end_year - 4)
    try:
        daily = _open_meteo_daily(
            "https://archive-api.open-meteo.com/v1/archive",
            lat, lon, f"{start_year}-01-01", f"{end_year}-12-31",
        )
        accum = {m: {"et0": [], "temp": []} for m in range(1, 13)}
        for i, day_text in enumerate(daily.get("time", [])):
            month = datetime.date.fromisoformat(day_text).month
            et0 = daily.get("et0_fao_evapotranspiration", [])[i]
            temp = daily.get("temperature_2m_mean", [])[i]
            if et0 is not None:
                accum[month]["et0"].append(float(et0))
            if temp is not None:
                accum[month]["temp"].append(float(temp))
        return {
            m: {
                "et0_mm_day": float(np.mean(values["et0"])) if values["et0"] else None,
                "temperature_c": float(np.mean(values["temp"])) if values["temp"] else None,
            }
            for m, values in accum.items()
        }
    except Exception:
        return {}


def fetch_et0_weather(gov, design_date):
    """Get daily FAO reference ET for the date, then fall back to monthly normals.

    Open-Meteo's daily ET0 field is the reference evapotranspiration of a
    well-watered grass surface. For dates outside the forecast window, the
    app uses a five-year same-month climate normal, not a claimed forecast.
    """
    loc = GOVERNORATE_DATA.get(gov, {})
    lat, lon = loc.get("lat"), loc.get("lon")
    normals = _monthly_et0_climatology(gov)
    result = {"et0_mm_day": None, "temperature_c": None, "monthly_et0": {},
              "source": "ET0 unavailable"}
    result["monthly_et0"] = {
        m: value.get("et0_mm_day") for m, value in normals.items()
        if value.get("et0_mm_day") is not None
    }
    today = datetime.date.today()
    endpoint = None
    source = None
    if lat is not None and lon is not None:
        if today <= design_date <= today + datetime.timedelta(days=16):
            endpoint = "https://api.open-meteo.com/v1/forecast"
            source = "Open-Meteo daily forecast"
        elif design_date < today:
            endpoint = "https://archive-api.open-meteo.com/v1/archive"
            source = "Open-Meteo historical archive"
        if endpoint:
            try:
                daily = _open_meteo_daily(endpoint, lat, lon,
                                          design_date.isoformat(), design_date.isoformat())
                times = daily.get("time", [])
                if times:
                    et0s = daily.get("et0_fao_evapotranspiration", [])
                    temps = daily.get("temperature_2m_mean", [])
                    if et0s and et0s[0] is not None:
                        result["et0_mm_day"] = float(et0s[0])
                        result["source"] = source
                    if temps and temps[0] is not None:
                        result["temperature_c"] = round(float(temps[0]), 1)
            except Exception:
                pass
    month_normal = normals.get(design_date.month, {})
    if result["et0_mm_day"] is None:
        result["et0_mm_day"] = month_normal.get("et0_mm_day")
        result["source"] = "Open-Meteo five-year monthly climate normal" if result["et0_mm_day"] is not None else "ET0 unavailable"
    if result["temperature_c"] is None:
        temp = month_normal.get("temperature_c")
        result["temperature_c"] = round(float(temp), 1) if temp is not None else None
    return result


# PART 5 — TRANSPARENT RULE-BASED SCORING
class RuleBasedJudge:
    """Transparent compatibility score; no synthetic training or accuracy claim."""

    def evaluate(self, recommended, water_budget, soil_type, avg_temp, lang="ar", water_data=None):
        T = TRANSLATIONS[lang]
        if recommended is None or len(recommended) == 0:
            return {"score": 0, "label": T["judge_avg"], "criteria": {},
                    "method": "rule-based", "co2_saved": 0}

        water_data = water_data or {}
        kc = float(water_data.get("kc_mean", np.mean(recommended["water"].map({1: .35, 2: .60, 3: .85}))))
        water_eff = float(np.clip((1.0 - kc) / 0.75, 0, 1))
        climate_fit = float(recommended.apply(
            lambda r: 1 if r["temp_min"] <= avg_temp <= r["temp_max"] else 0, axis=1
        ).mean())
        soil_fit = float(recommended.apply(
            lambda r: 1 if ("any" in r["soil"] or soil_type in r["soil"]) else 0.5,
            axis=1
        ).mean())
        diversity = min(len(recommended["use"].unique()) / 5.0, 1.0)
        beauty_avg = float(np.clip((recommended["beauty"].mean() - 1) / 4.0, 0, 1))
        co2_score = float(np.clip(recommended["co2"].mean() / 60.0, 0, 1))
        score = round(water_eff * 30 + climate_fit * 25 + soil_fit * 20
                      + diversity * 10 + beauty_avg * 8 + co2_score * 7)
        if score >= 75:
            label = T["judge_excellent"]
        elif score >= 50:
            label = T["judge_good"]
        else:
            label = T["judge_avg"]
        criteria = {
            T["judge_water_eff"]: round(water_eff * 100),
            T["judge_climate"]: round(climate_fit * 100),
            T["judge_soil"]: round(soil_fit * 100),
            T["judge_diversity"]: round(diversity * 100),
            T["judge_beauty"]: round(beauty_avg * 100),
        }
        return {
            "score": score,
            "label": label,
            "criteria": criteria,
            "method": "rule-based",
            "co2_saved": round(float(recommended["co2"].sum())),
        }


# PART 6 — RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

# Soil-compatibility rules (SOIL_COMPAT) are loaded from the soil_compatibility table.
def recommend_plants(df, water_budget, soil_type, temp_avg, top_n=8):
    valid = SOIL_COMPAT.get(soil_type, ["any"])
    results = []
    for _, row in df.iterrows():
        soils = row['soil']
        if isinstance(soils, str):
            soils = [soils]
        soil_ok = ("any" in soils) or any(s in valid for s in soils)
        if (
            row['water'] <= water_budget and
            row['temp_min'] <= temp_avg <= row['temp_max'] and
            soil_ok
        ):
            score = row['beauty'] * (4 - row['water']) + row.get('co2', 10) / 10
            results.append({**row.to_dict(), 'rec_score': score})

    if not results:
        for _, row in df.iterrows():
            if row['water'] <= water_budget:
                results.append({**row.to_dict(), 'rec_score': row['beauty']})
    if not results:
        # Last resort so the app never shows an empty design: lowest-water plants first.
        for _, row in df.sort_values(['water', 'beauty'], ascending=[True, False]).iterrows():
            results.append({**row.to_dict(), 'rec_score': row['beauty']})
    if not results:
        return df.iloc[0:0].assign(rec_score=pd.Series(dtype=float))

    res_df = pd.DataFrame(results).sort_values('rec_score', ascending=False, kind='stable')
    # تنويع الأنواع — take the best plant of each type first, then fill the
    # remaining places with the next-best plants of any type.
    picked, used_types = [], set()
    for _, row in res_df.iterrows():
        if len(picked) >= top_n:
            break
        if row['use'] not in used_types:
            picked.append(row)
            used_types.add(row['use'])
    picked_names = {row['name'] for row in picked}
    for _, row in res_df.iterrows():
        if len(picked) >= top_n:
            break
        if row['name'] not in picked_names:
            picked.append(row)
            picked_names.add(row['name'])
    return (pd.DataFrame(picked).sort_values('rec_score', ascending=False, kind='stable')
            .reset_index(drop=True))


# ═══════════════════════════════════════════════════════════════════════════════
# PART 7 — LAYOUT VISUALIZATION (3D-style)
# ═══════════════════════════════════════════════════════════════════════════════

def _strip_emoji(text):
    """Remove emoji, which the chart font cannot draw (they appear as empty boxes)."""
    return "".join(ch for ch in str(text)
                   if not (ord(ch) >= 0x1F000 or 0x2600 <= ord(ch) <= 0x27BF or ch in "\ufe0f\u200d")).strip()


def generate_layout(plants_df, area_w, area_h, gov, region, season_str, lang="ar", unit="m"):
    T = TRANSLATIONS[lang]
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor('#060f07')
    ax.set_facecolor('#0d1a0f')

    # ── 3D perspective background panels ──────────────────────────────────
    # رسم طبقات عمق للإيهام بالبُعد الثالث
    for depth, alpha, y_off in [(0.92, 0.15, 0.02),(0.94, 0.10, 0.01),(0.96, 0.06, 0.00)]:
        shadow = FancyBboxPatch(
            (0.02 + depth * 0.01, 0.05 - y_off), 0.96, 0.90,
            boxstyle="round,pad=0.01",
            linewidth=0, facecolor='#00e676', alpha=alpha, zorder=0
        )
        ax.add_patch(shadow)

    # الإطار الرئيسي
    bg = FancyBboxPatch(
        (0.03, 0.06), 0.94, 0.88,
        boxstyle="round,pad=0.01",
        linewidth=2.5, edgecolor='#00e676',
        facecolor='#0f2010', zorder=1
    )
    ax.add_patch(bg)

    # ── شبكة منظور ────────────────────────────────────────────────────────
    for gx in np.arange(0.05, 0.98, 0.07):
        ax.axvline(gx, color='#1a3a1d', lw=0.4, alpha=0.6, zorder=2)
    for gy in np.arange(0.08, 0.95, 0.07):
        ax.axhline(gy, color='#1a3a1d', lw=0.4, alpha=0.6, zorder=2)

    # ── عنوان بياني ────────────────────────────────────────────────────────
    title_str = f"{gov} / {region}"
    season_txt = _strip_emoji(season_str)
    dim_txt    = f"{float(area_w):g} × {float(area_h):g} {'km' if unit == 'km' else 'm'}"
    ax.text(0.5, 0.975, title_str,
            ha='center', va='top', fontsize=14, fontweight='bold',
            color='#69f0ae', transform=ax.transAxes,
            fontfamily='DejaVu Sans',
            path_effects=[pe.withStroke(linewidth=3, foreground='#000')])
    # Season and size are drawn separately so Arabic text cannot reorder the numbers.
    season_x, dim_x = (0.51, 0.49) if lang == "ar" else (0.49, 0.51)
    ax.text(season_x, 0.952, season_txt,
            ha='left' if lang == "ar" else 'right', va='top', fontsize=9,
            color='#b9f6ca', transform=ax.transAxes,
            fontfamily='DejaVu Sans')
    ax.text(dim_x, 0.952, dim_txt,
            ha='right' if lang == "ar" else 'left', va='top', fontsize=9,
            color='#b9f6ca', transform=ax.transAxes,
            fontfamily='DejaVu Sans')

    # ── ألوان وأشكال ──────────────────────────────────────────────────────
    color_map = {
        'شجرة':            '#00c853',
        'شجيرة':           '#76ff03',
        'متسلق':           '#aeea00',
        'غطاء أرضي':      '#ccff90',
        'سياج':            '#1b5e20',
        'عشب':             '#64dd17',
        'زينة':            '#ffd600',
        'زهور موسمية':     '#f50057',
        'نباتات مائية':    '#00b0ff',
        'نباتات عطرية':    '#e040fb',
        'نباتات ظل':       '#8d6e63',
    }
    marker_map = {
        'شجرة':           ('o',  320),
        'شجيرة':          ('s',  200),
        'متسلق':          ('^',  160),
        'غطاء أرضي':     ('p',  130),
        'سياج':           ('D',  160),
        'عشب':            ('h',  130),
        'زينة':           ('*',  260),
        'زهور موسمية':    ('8',  160),
        'نباتات مائية':   ('v',  170),
        'نباتات عطرية':   ('+',  170),
        'نباتات ظل':      ('x',  160),
    }

    # مواضع 3D موزعة
    positions = [
        (0.12, 0.80), (0.50, 0.83), (0.88, 0.80),
        (0.12, 0.22), (0.50, 0.18), (0.88, 0.22),
        (0.88, 0.50), (0.12, 0.50),
    ]

    for i, (_, plant) in enumerate(plants_df.iterrows()):
        if i >= len(positions):
            break
        x, y = positions[i]
        use   = plant['use']
        col   = color_map.get(use, '#69f0ae')
        shp, sz = marker_map.get(use, ('o', 180))

        # هالة توهج متعددة الطبقات (3D glow)
        for radius, alpha_val in [(0.12, 0.04), (0.09, 0.07), (0.06, 0.12), (0.04, 0.18)]:
            glow = plt.Circle((x, y), radius, color=col, alpha=alpha_val, zorder=2)
            ax.add_patch(glow)

        # ظل النبتة (3D effect)
        ax.scatter(x + 0.008, y - 0.012, c='#000000', marker=shp,
                   s=sz * 2.8, zorder=3, alpha=0.35)

        # الرمز الأساسي
        ax.scatter(x, y, c=col, marker=shp, s=sz * 3,
                   zorder=5, edgecolors='white', linewidths=1.5, alpha=0.95)

        # اسم النبات
        label = plant['name_en'] if lang == 'en' else plant['name']
        ax.text(x, y - 0.13, label,
                ha='center', va='top', fontsize=7.5,
                color='#e8f5e9', fontfamily='DejaVu Sans',
                bbox=dict(
                    boxstyle='round,pad=0.25',
                    facecolor='#060f07', alpha=0.88,
                    edgecolor=col, linewidth=0.8
                ),
                zorder=6,
                path_effects=[pe.withStroke(linewidth=1, foreground='#000')])

        # Water need as 1-3 blue dots (emoji are not available in the chart font).
        level = int(plant['water']) if pd.notna(plant['water']) else 1
        dots_x = [x + (k - (level - 1) / 2) * 0.018 for k in range(level)]
        ax.scatter(dots_x, [y + 0.125] * level, s=28, c='#29b6f6',
                   edgecolors='white', linewidths=0.6, zorder=6)

    # ── ممر مركزي 3D ──────────────────────────────────────────────────────
    path_shadow = FancyBboxPatch(
        (0.39, 0.35), 0.22, 0.30,
        boxstyle="round,pad=0.01",
        linewidth=0, facecolor='#000', alpha=0.3, zorder=3
    )
    ax.add_patch(path_shadow)
    path_p = FancyBboxPatch(
        (0.40, 0.36), 0.20, 0.28,
        boxstyle="round,pad=0.01",
        linewidth=1.5, edgecolor='#795548',
        facecolor='#1a1205', zorder=3, alpha=0.92
    )
    ax.add_patch(path_p)
    ax.text(0.50, 0.50, T["path"],
            ha='center', va='center', fontsize=9,
            color='#bcaaa4', fontfamily='DejaVu Sans', zorder=4,
            fontweight='bold')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')

    # ── legend ──────────────────────────────────────────────────────────────
    handles = []
    for _, plant in plants_df.iterrows():
        col = color_map.get(plant['use'], '#69f0ae')
        lbl = plant['name_en'] if lang == 'en' else plant['name']
        handles.append(mpatches.Patch(color=col, label=lbl))

    ax.legend(
        handles=handles, loc='upper center',
        bbox_to_anchor=(0.5, -0.02), ncol=4,
        fontsize=7.5, framealpha=0.92,
        edgecolor='#4caf50', facecolor='#060f07',
        labelcolor='#e8f5e9',
        prop={'family': 'DejaVu Sans', 'size': 7.5}
    )

    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# PART 8 — WATER CALCULATION
# ═══════════════════════════════════════════════════════════════════════════════

# Planning coefficients by broad landscape functional group. These are explicit
# starting assumptions for a demo, not species-specific FAO table values or
# locally measured coefficients. FAO-56 defines ETc = Kc × ET0; Kc must be
# calibrated to crop/cover, growth stage, density and local conditions.
# See https://www.fao.org/4/x0490E/x0490e0a.htm and
# https://www.fao.org/4/x0490e/x0490e0b.htm
# Values are loaded from the plant_use_categories table (LANDSCAPE_KC_BY_USE).
WEEKS_PER_MONTH = 365.25 / 12 / 7   # ≈ 4.35


def estimated_landscape_kc(plant):
    """Return the provisional group Kc assigned to one catalog plant."""
    return LANDSCAPE_KC_BY_USE.get(str(plant.get("use", "")), 0.55)


def calc_water(recommended, area_sqm, et0_mm_day=None, et0_monthly=None, target_year=None):
    """Estimate irrigation from ET0 × provisional landscape Kc.

    mm × m² = litres. The result assumes equal area share per recommended plant,
    90% application efficiency, and no rainfall credit. Annual values use the
    supplied monthly climate normals when available. The legacy tier method is
    only a clearly flagged fallback when weather ET0 cannot be fetched.
    """
    area_sqm = max(0.0, float(area_sqm or 0))
    kc_values = [estimated_landscape_kc(row) for _, row in recommended.iterrows()] if len(recommended) else []
    kc_mean = float(np.mean(kc_values)) if kc_values else 0.55
    efficiency = 0.90
    baseline_kc = 0.85  # explicit high-water landscape comparison assumption
    et0_monthly = et0_monthly or {}
    target_year = int(target_year or datetime.date.today().year)
    has_et0 = et0_mm_day is not None and float(et0_mm_day) >= 0

    if has_et0:
        daily_et0 = float(et0_mm_day)
        ai_w = round(daily_et0 * kc_mean * area_sqm / efficiency * 7)
        trad_w = round(daily_et0 * baseline_kc * area_sqm / efficiency * 7)
        valid_months = [float(et0_monthly[m]) for m in range(1, 13)
                        if et0_monthly.get(m) is not None]
        if len(valid_months) == 12:
            et0_year_mm = sum(float(et0_monthly[m]) * calendar.monthrange(target_year, m)[1]
                              for m in range(1, 13))
            annual_basis = "monthly climate normals"
        else:
            et0_year_mm = daily_et0 * (366 if calendar.isleap(target_year) else 365)
            annual_basis = "selected-day annualized estimate"
        ai_y = round(et0_year_mm * kc_mean * area_sqm / efficiency)
        trad_y = round(et0_year_mm * baseline_kc * area_sqm / efficiency)
        method = "ET0 × provisional functional-group Kc"
        fallback = False
    else:
        # Kept solely so users still see an estimate during an API outage;
        # the interface flags it as non-weather-based and non-scientific.
        average_class = float(recommended["water"].mean()) if len(recommended) else 2.0
        legacy_rates = {1: 3.5, 2: 7.0, 3: 12.0}
        ai_rate = legacy_rates.get(round(average_class), 7.0)
        trad_rate = 12.0
        ai_w = round(ai_rate * area_sqm)
        trad_w = round(trad_rate * area_sqm)
        ai_y = ai_w * 52
        trad_y = trad_w * 52
        daily_et0 = None
        annual_basis = "legacy ordinal fallback"
        method = "Legacy fallback (ET0 unavailable)"
        fallback = True

    pct = round((trad_w - ai_w) / trad_w * 100, 1) if trad_w > 0 else 0
    return {
        "ai_w": ai_w, "trad_w": trad_w, "pct": pct,
        "saved_w": trad_w - ai_w, "ai_y": ai_y, "trad_y": trad_y,
        "kc_mean": round(kc_mean, 3), "baseline_kc": baseline_kc,
        "efficiency": efficiency, "et0_mm_day": round(daily_et0, 2) if daily_et0 is not None else None,
        "annual_basis": annual_basis, "method": method, "fallback": fallback,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PART 9 — FEEDBACK STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

APP_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(APP_DIR, "hassouna_feedback.json")
LEGACY_FEEDBACK_FILE = os.path.join(APP_DIR, "isef_feedback.json")   # older versions' file name


def save_feedback(gov, region, rating, comment, score, lang):
    """Append one rating; returns True on success, False if the file cannot be written."""
    record = {
        "timestamp":   str(datetime.datetime.now()),
        "governorate": gov,
        "region":      region,
        "rating":      rating,
        "comment":     comment,
        "judge_score": score,
        "lang":        lang,
    }
    data = load_feedback_stats()
    data.append(record)
    try:
        tmp = FEEDBACK_FILE + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, FEEDBACK_FILE)   # atomic: a crash cannot leave a half-written file
        return True
    except OSError:
        return False


def load_feedback_stats():
    for path in (FEEDBACK_FILE, LEGACY_FEEDBACK_FILE):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except Exception:
                return []
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# PART 10 — CSS INJECTION (Ultra Design)
# ═══════════════════════════════════════════════════════════════════════════════

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Tajawal:wght@400;700;800&display=swap');

    :root {
        --dark:      #060f07;
        --darker:    #030807;
        --card:      #0c1f12;
        --card2:     #0f2a18;
        --green1:    #00e676;
        --green2:    #69f0ae;
        --green3:    #b9f6ca;
        --accent:    #00bfa5;
        --gold:      #ffd600;
        --red:       #ff5252;
        --text:      #e8f5e9;
        --textSub:   #81c784;
        --border:    rgba(0,230,118,0.22);
        --border2:   rgba(0,230,118,0.12);
        --shadow:    0 8px 32px rgba(0,0,0,0.6);
    }

    html, body, [class*="css"] {
        font-family: 'Cairo','Tajawal',sans-serif !important;
        direction: rtl;
        background: var(--darker) !important;
        color: var(--text) !important;
    }
    /* Custom scrollbar only where a mouse is used. On touch screens a styled scrollbar
       stays visible all the time as a green line that follows the scroll position. */
    @media (hover: hover) and (pointer: fine) {
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: var(--darker); }
        ::-webkit-scrollbar-thumb { background: var(--green1); border-radius: 3px; }
    }

    .main > div:first-child {
        background:
            radial-gradient(ellipse at 10% 20%, rgba(0,230,118,0.05) 0%, transparent 55%),
            radial-gradient(ellipse at 90% 80%, rgba(0,191,165,0.04) 0%, transparent 55%),
            var(--darker) !important;
    }

    /* ══ INTRO SCREEN ══════════════════════════════════════════════════════ */
    .intro-overlay {
        position: fixed; inset: 0; z-index: 9999;
        background: radial-gradient(ellipse at 50% 50%, #04180a 0%, #020c05 100%);
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        pointer-events: none;
        animation: intro-fade-in 0.8s ease, intro-fade-out 0.9s ease 3.4s forwards;
    }
    @keyframes intro-fade-in { from{opacity:0} to{opacity:1} }
    @keyframes intro-fade-out { to { opacity: 0; visibility: hidden; } }

    .intro-logo-ring {
        width: 180px; height: 180px;
        border-radius: 50%;
        border: 3px solid transparent;
        background:
            linear-gradient(#04180a,#04180a) padding-box,
            conic-gradient(from 0deg, #00e676, #ffd600, #00e676) border-box;
        display: flex; align-items: center; justify-content: center;
        animation: ring-spin 6s linear infinite;
        box-shadow: 0 0 60px rgba(0,230,118,0.3), 0 0 120px rgba(0,230,118,0.15);
        margin-bottom: 2rem;
    }
    @keyframes ring-spin { to { filter: hue-rotate(360deg); } }

    .intro-logo-inner {
        width: 150px; height: 150px;
        border-radius: 50%;
        background: radial-gradient(circle, #0a2a12 0%, #04180a 100%);
        display: flex; align-items: center; justify-content: center;
        font-size: 4rem;
    }

    .intro-title {
        font-size: clamp(1.8rem, 4vw, 3rem);
        font-weight: 900;
        background: linear-gradient(135deg, #00e676 0%, #69f0ae 40%, #ffd600 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        letter-spacing: -0.5px;
        animation: title-zoom 0.6s cubic-bezier(.34,1.56,.64,1) 0.3s both;
        margin-bottom: 0.5rem;
    }
    @keyframes title-zoom {
        from { transform: scale(0.7); opacity: 0; }
        to   { transform: scale(1);   opacity: 1; }
    }

    .intro-isef {
        font-size: 1.5rem; font-weight: 700;
        color: #ffd600;
        text-align: center;
        animation: title-zoom 0.6s cubic-bezier(.34,1.56,.64,1) 0.5s both;
        filter: drop-shadow(0 0 12px rgba(255,214,0,0.6));
        margin-bottom: 1rem;
    }

    .intro-sub {
        color: var(--textSub);
        font-size: 1rem;
        text-align: center;
        max-width: 500px;
        animation: title-zoom 0.6s ease 0.7s both;
        margin-bottom: 2.5rem;
    }

    .intro-progress-bar {
        width: 300px; height: 4px;
        background: rgba(0,230,118,0.15);
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 1.5rem;
    }
    .intro-progress-inner {
        height: 100%; border-radius: 4px;
        background: linear-gradient(90deg, var(--green1), var(--gold));
        animation: progress-run 3.5s ease-out forwards;
    }
    @keyframes progress-run { from{width:0} to{width:100%} }

    .intro-particles {
        position: absolute; inset: 0; overflow: hidden; pointer-events: none;
    }

    /* ══ HEADER ══════════════════════════════════════════════════════════ */
    .main-header {
        background: linear-gradient(135deg, #020d07 0%, #041a0c 50%, #071f0f 100%);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 2rem 2rem 1.6rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        margin-bottom: 1.5rem;
        box-shadow:
            0 0 60px rgba(0,230,118,0.08),
            0 0 120px rgba(0,230,118,0.04),
            inset 0 1px 0 rgba(0,230,118,0.15);
    }
    .main-header::before {
        content:'';
        position:absolute; top:0; left:50%; transform:translateX(-50%);
        width:80%; height:1px;
        background: linear-gradient(90deg, transparent, var(--green1), transparent);
    }
    .main-header::after {
        content:''; position:absolute; inset:0;
        background: radial-gradient(ellipse at 50% -10%, rgba(0,230,118,0.07) 0%, transparent 65%);
        pointer-events:none;
    }
    .main-header h1 {
        font-size: clamp(1.4rem, 3.2vw, 2.2rem);
        font-weight: 900;
        background: linear-gradient(135deg, #00e676 0%, #69f0ae 40%, #ffd600 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.5rem;
        animation: title-glow 4s ease-in-out infinite;
    }
    @keyframes title-glow {
        0%,100% { filter: drop-shadow(0 0 8px rgba(0,230,118,0.3)); }
        50%      { filter: drop-shadow(0 0 18px rgba(0,230,118,0.7)); }
    }
    .main-header p { color: var(--textSub); font-size: 0.95rem; margin: 0; }
    .isef-badge {
        display: inline-block;
        background: linear-gradient(90deg, #ffd600, #ff8f00);
        color: #000 !important;
        padding: 0.3rem 1.3rem;
        border-radius: 24px;
        font-size: 0.82rem; font-weight: 800;
        margin-top: 0.7rem;
        box-shadow: 0 0 20px rgba(255,214,0,0.5);
        animation: badge-pulse 2.5s ease-in-out infinite;
        letter-spacing: 1px;
    }
    @keyframes badge-pulse {
        0%,100% { box-shadow: 0 0 20px rgba(255,214,0,0.5); transform: scale(1); }
        50%      { box-shadow: 0 0 38px rgba(255,214,0,0.8); transform: scale(1.04); }
    }

    /* ══ STEP WIZARD ════════════════════════════════════════════════════ */
    .step-wizard {
        display: flex; align-items: center; justify-content: center;
        gap: 0; margin: 1.5rem 0 2rem;
        flex-wrap: wrap;
    }
    .step-item {
        display: flex; align-items: center;
    }
    .step-circle {
        width: 44px; height: 44px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 1rem;
        border: 2px solid;
        transition: all .3s;
        position: relative;
    }
    .step-circle.done {
        background: linear-gradient(135deg, #00c853, #00897b);
        border-color: #00c853;
        color: #fff;
        box-shadow: 0 0 18px rgba(0,200,83,0.5);
    }
    .step-circle.active {
        background: rgba(0,230,118,0.1);
        border-color: var(--green1);
        color: var(--green1);
        box-shadow: 0 0 18px rgba(0,230,118,0.35);
        animation: step-pulse 2s ease-in-out infinite;
    }
    .step-circle.pending {
        background: rgba(0,230,118,0.04);
        border-color: rgba(0,230,118,0.2);
        color: #3a6a4a;
    }
    @keyframes step-pulse {
        0%,100% { box-shadow: 0 0 18px rgba(0,230,118,0.35); }
        50%      { box-shadow: 0 0 30px rgba(0,230,118,0.6); }
    }
    .step-label {
        font-size: 0.78rem; color: var(--textSub);
        text-align: center; margin-top: 4px;
        font-weight: 600;
    }
    .step-label.active-label { color: var(--green1); }
    .step-connector {
        width: 60px; height: 2px;
        background: rgba(0,230,118,0.15);
        margin: 0 4px;
        position: relative; overflow: hidden;
    }
    .step-connector.done-connector {
        background: linear-gradient(90deg, #00c853, #00897b);
    }
    .step-connector::after {
        content: '';
        position: absolute; inset: 0;
        background: linear-gradient(90deg, transparent, rgba(0,230,118,0.4), transparent);
        animation: shimmer 2s infinite;
    }
    @keyframes shimmer { from{transform:translateX(-100%)} to{transform:translateX(100%)} }

    /* ══ FORM CARD ══════════════════════════════════════════════════════ */
    .form-card {
        background: linear-gradient(135deg, #0a1a0d 0%, #0d2214 100%);
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 2rem;
        margin: 0 auto 1.5rem;
        max-width: 900px;
        position: relative;
        overflow: hidden;
        box-shadow: var(--shadow);
        animation: card-in 0.4s ease both;
    }
    @keyframes card-in {
        from { opacity:0; transform: translateY(20px); }
        to   { opacity:1; transform: translateY(0); }
    }
    .form-card::before {
        content:''; position:absolute; top:0; left:50%; transform:translateX(-50%);
        width:60%; height:1px;
        background: linear-gradient(90deg, transparent, var(--green1), transparent);
    }
    .form-card-title {
        font-size: 1.25rem; font-weight: 800;
        color: var(--green2); margin-bottom: 1.5rem;
        padding-bottom: 0.7rem;
        border-bottom: 1px solid rgba(0,230,118,0.15);
    }

    /* ══ INFO PILL ══════════════════════════════════════════════════════ */
    .info-pill {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(0,230,118,0.08);
        border: 1px solid rgba(0,230,118,0.2);
        border-radius: 30px;
        padding: 0.35rem 1rem;
        font-size: 0.85rem; color: var(--green2);
        margin: 0.2rem;
        transition: all .25s;
    }
    .info-pill:hover {
        background: rgba(0,230,118,0.15);
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(0,230,118,0.2);
    }

    /* ══ METRICS ════════════════════════════════════════════════════════ */
    [data-testid="metric-container"] {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 18px !important;
        padding: 1.2rem !important;
        transition: transform .25s, box-shadow .25s;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 14px 36px rgba(0,230,118,0.2);
    }
    [data-testid="stMetricValue"] {
        color: var(--green1) !important;
        font-size: 1.75rem !important;
        font-weight: 900 !important;
    }
    [data-testid="stMetricLabel"] { color: var(--textSub) !important; font-size: 0.8rem !important; }
    [data-testid="stMetricDelta"]  { color: var(--accent) !important; }

    /* ══ SAVING BANNER ══════════════════════════════════════════════════ */
    .saving-banner {
        background: linear-gradient(135deg, rgba(0,230,118,0.08) 0%, rgba(0,191,165,0.05) 100%);
        border: 1px solid rgba(0,230,118,0.3);
        border-radius: 20px;
        padding: 1.5rem 1rem;
        text-align: center;
        margin: 1rem 0;
        position: relative; overflow: hidden;
    }
    .saving-banner::before {
        content:''; position:absolute; top:0; left:50%; transform:translateX(-50%);
        width:60%; height:1px;
        background: linear-gradient(90deg, transparent, var(--green1), transparent);
    }
    .saving-big {
        font-size: 3.5rem; font-weight: 900;
        background: linear-gradient(90deg, var(--green1), var(--gold));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 12px rgba(0,230,118,0.4));
    }

    /* ══ PLANT CARDS ════════════════════════════════════════════════════ */
    .plant-card {
        background: var(--card);
        border: 1px solid var(--border2);
        border-radius: 18px;
        padding: 1rem 0.6rem;
        text-align: center;
        transition: transform .3s cubic-bezier(.34,1.56,.64,1), box-shadow .3s, border-color .3s;
        cursor: default;
        animation: float-in 0.5s ease both;
        position: relative; overflow: hidden;
    }
    .plant-card::before {
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background: linear-gradient(90deg, transparent, var(--green1), transparent);
        opacity: 0; transition: opacity .3s;
    }
    .plant-card:hover {
        transform: translateY(-8px) scale(1.04);
        box-shadow: 0 20px 44px rgba(0,230,118,0.22), 0 0 0 1px var(--green1);
        border-color: var(--green1);
    }
    .plant-card:hover::before { opacity: 1; }
    @keyframes float-in {
        from { opacity:0; transform: translateY(28px) scale(.96); }
        to   { opacity:1; transform: translateY(0) scale(1); }
    }
    .plant-name { color: var(--green2); font-weight: 700; font-size: 1rem; margin: .3rem 0 .1rem; }
    .plant-en   { color: #4a7a5a; font-size: 0.74rem; }
    .plant-temp { color: #3a6a4a; font-size: 0.72rem; margin-top: 3px; }

    /* ══ JUDGE CARD ═════════════════════════════════════════════════════ */
    .judge-card {
        background: linear-gradient(135deg, #071a14 0%, #09221a 100%);
        border: 1px solid rgba(0,191,165,0.3);
        border-radius: 22px;
        padding: 1.8rem;
        margin: 0.5rem 0 1rem;
        position: relative; overflow: hidden;
        box-shadow: var(--shadow);
    }
    .judge-card::before {
        content:''; position:absolute; top:0; left:50%; transform:translateX(-50%);
        width:50%; height:1px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
    }
    .judge-score {
        font-size: 4.5rem; font-weight: 900;
        color: var(--gold);
        text-align: center; line-height: 1;
        filter: drop-shadow(0 0 18px rgba(255,214,0,0.55));
        animation: score-in 0.7s cubic-bezier(.34,1.56,.64,1) both;
    }
    @keyframes score-in {
        from { transform: scale(0.4); opacity: 0; }
        to   { transform: scale(1);   opacity: 1; }
    }
    .judge-label { text-align: center; color: var(--accent); font-size: 1.05rem; font-weight: 700; margin-top: .5rem; }
    .criteria-bar { display: flex; align-items: center; gap: 10px; margin: .5rem 0; }
    .criteria-name { color: var(--textSub); font-size: .86rem; min-width: 155px; text-align: right; }
    .bar-outer {
        flex: 1;
        background: rgba(0,230,118,0.07);
        border: 1px solid rgba(0,230,118,0.12);
        border-radius: 10px; height: 9px; overflow: hidden;
    }
    .bar-inner {
        height: 100%; border-radius: 10px;
        background: linear-gradient(90deg, var(--accent), var(--green1));
        animation: bar-grow 1.4s ease both;
    }
    @keyframes bar-grow { from{width:0!important} }
    .bar-val { color: var(--green1); font-size: .82rem; font-weight: 700; min-width: 40px; text-align: left; }

    /* ══ SUMMARY BOX ════════════════════════════════════════════════════ */
    .summary-box {
        background: var(--card);
        border: 1px solid var(--border2);
        border-radius: 20px;
        padding: 1.5rem;
        margin-top: 1rem;
        position: relative; overflow: hidden;
    }
    .summary-box::before {
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background: linear-gradient(90deg, transparent, var(--green1), transparent);
    }
    .summary-title {
        font-size: 1.1rem; font-weight: 800;
        color: var(--green1);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(0,230,118,0.15);
    }
    .summary-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: .44rem 0;
        border-bottom: 1px solid rgba(0,230,118,0.07);
        font-size: .9rem;
    }
    .summary-row:last-child { border-bottom: none; }
    .summary-row span { color: var(--textSub); }
    .summary-row b    { color: var(--text); font-weight: 600; }

    /* ══ STATUS BAR ═════════════════════════════════════════════════════ */
    .status-bar {
        background: var(--card);
        border: 1px solid var(--border2);
        border-radius: 16px;
        padding: .8rem 1rem;
        margin-bottom: 1rem;
        display: flex; flex-wrap: wrap; gap: .5rem;
        align-items: center; justify-content: center;
    }
    .status-chip {
        background: rgba(0,230,118,0.08);
        border: 1px solid rgba(0,230,118,0.2);
        border-radius: 20px;
        padding: .22rem .8rem;
        font-size: .82rem; color: var(--green2);
        white-space: nowrap;
    }

    /* ══ STATS CARDS ════════════════════════════════════════════════════ */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .stats-card {
        background: var(--card);
        border: 1px solid var(--border2);
        border-radius: 16px;
        padding: 1.2rem;
        text-align: center;
        transition: transform .25s, box-shadow .25s;
    }
    .stats-card:hover { transform: translateY(-4px); box-shadow: 0 10px 28px rgba(0,230,118,0.18); }
    .stats-num { font-size: 2.2rem; font-weight: 900; color: var(--gold); }
    .stats-lbl { font-size: .82rem; color: var(--textSub); margin-top: 2px; }

    /* ══ FEEDBACK ════════════════════════════════════════════════════════ */
    .feedback-box {
        background: linear-gradient(135deg, #0d1a0a 0%, #0a1508 100%);
        border: 1px solid rgba(255,214,0,0.2);
        border-radius: 20px; padding: 1.5rem; margin-top: 1rem;
    }

    /* ══ SIDEBAR ═════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #030a06 0%, #050f08 100%) !important;
        border-left: 1px solid var(--border2) !important;
    }
    [data-testid="stSidebar"] * { color: var(--textSub) !important; }
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stNumberInput input,
    [data-testid="stSidebar"] .stTextInput input {
        background: rgba(0,230,118,0.04) !important;
        border: 1px solid var(--border2) !important;
        color: var(--text) !important;
        border-radius: 9px !important;
    }

    /* ══ BUTTONS ═════════════════════════════════════════════════════════ */
    .stButton > button {
        background: linear-gradient(135deg, #00c853 0%, #00897b 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: .7rem 1.6rem !important;
        transition: all .25s !important;
        box-shadow: 0 5px 20px rgba(0,200,83,0.38) !important;
        letter-spacing: .3px !important;
    }
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 32px rgba(0,200,83,0.58) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* ══ RADIO / SELECT ══════════════════════════════════════════════════ */
    .stRadio label, .stRadio div { color: var(--textSub) !important; }
    .stTextArea textarea {
        background: var(--card) !important;
        border: 1px solid var(--border2) !important;
        color: var(--text) !important;
        border-radius: 10px !important;
    }
    .stAlert { border-radius: 14px !important; }
    h3 { color: var(--green2) !important; font-weight: 700 !important; }

    /* ══ TABLE OVERRIDES ═════════════════════════════════════════════════ */
    .dataframe, table {
        background: var(--card) !important;
        color: var(--text) !important;
        border-color: var(--border2) !important;
    }
    .dataframe th, table th {
        background: rgba(0,230,118,0.1) !important;
        color: var(--green2) !important;
        border-color: var(--border2) !important;
    }
    .dataframe td, table td {
        background: var(--card) !important;
        color: var(--text) !important;
        border-color: var(--border2) !important;
    }

    /* ══ LIVE DOT ════════════════════════════════════════════════════════ */
    .live-dot {
        display: inline-block; width: 8px; height: 8px;
        background: var(--green1); border-radius: 50%;
        margin-right: 4px;
        animation: blink 1.2s ease-in-out infinite;
    }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.1} }

    /* ══ CO2 BADGE ════════════════════════════════════════════════════════ */
    .co2-badge {
        display: inline-block;
        background: linear-gradient(90deg, rgba(0,230,118,0.12), rgba(0,191,165,0.08));
        border: 1px solid rgba(0,230,118,0.25);
        border-radius: 20px;
        padding: .3rem 1rem;
        font-size: .85rem; color: var(--green2);
        margin: .3rem 0;
    }

    /* ══ HIDE UI ═════════════════════════════════════════════════════════ */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem !important; }

    /* ══ CREATORS CREDIT ═════════════════════════════════════════════════ */
    .creators {
        display: flex; flex-wrap: wrap; justify-content: center; align-items: baseline;
        gap: .2rem .5rem; margin-top: .9rem;
        font-size: .92rem; color: var(--textSub);
    }
    .creators .creator-name { color: var(--green3); font-weight: 700; }
    .creators .creator-pair, .creators .creator-name { white-space: nowrap; }
    .intro-creators { margin: -1.2rem 0 2rem; padding: 0 1rem; }

    /* ══ PLANT GRID (replaces st.columns so it can reflow on small screens) ═ */
    .plant-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: .8rem; margin: .5rem 0 1rem;
    }

    /* ══ FIGURES: full width on desktop, swipeable on phones ═════════════ */
    .fig-scroll {
        overflow-x: auto; -webkit-overflow-scrolling: touch;
        border: 1px solid var(--border2); border-radius: 14px;
        direction: ltr;
    }
    .fig-scroll img { display: block; width: 100%; height: auto; }
    .fig-hint { display: none; font-size: .78rem; color: var(--textSub); margin: .2rem 0 .4rem; }

    /* ══ TABLETS (≤ 900px) ═══════════════════════════════════════════════ */
    @media (max-width: 900px) {
        .block-container, [data-testid="stMainBlockContainer"] {
            padding-left: 1.2rem !important; padding-right: 1.2rem !important;
            padding-top: 1rem !important;
        }
        .plant-grid { grid-template-columns: repeat(3, 1fr); }
        .form-card { padding: 1.5rem; }
        .main-header { padding: 1.5rem 1.2rem 1.2rem; }
    }

    /* ══ PHONES (≤ 640px) ════════════════════════════════════════════════ */
    @media (max-width: 640px) {
        .block-container, [data-testid="stMainBlockContainer"] {
            padding-left: .8rem !important; padding-right: .8rem !important;
            padding-top: .8rem !important;
        }
        .main-header { border-radius: 18px; padding: 1.2rem .9rem 1rem; margin-bottom: 1rem; }
        .main-header p { font-size: .85rem; }
        .isef-badge { font-size: .75rem; padding: .25rem 1rem; }
        .creators { font-size: .85rem; margin-top: .7rem; }

        .step-wizard { flex-wrap: nowrap; margin: 1rem 0 1.4rem; }
        .step-circle { width: 34px; height: 34px; font-size: .9rem; }
        .step-label { font-size: .66rem; max-width: 62px; line-height: 1.25; }
        .step-connector { width: 10px; margin: 0 2px; }

        .form-card { padding: 1.1rem .9rem; border-radius: 18px; }
        .form-card-title { font-size: 1.05rem; margin-bottom: 1rem; }
        .info-pill { font-size: .78rem; padding: .3rem .7rem; }

        .plant-grid { grid-template-columns: repeat(2, 1fr); gap: .6rem; }
        .plant-card { padding: .8rem .4rem; }

        .saving-big { font-size: 2.3rem; }
        .judge-card { padding: 1.2rem .9rem; border-radius: 18px; }
        .judge-score { font-size: 3.2rem; }
        .criteria-bar { flex-wrap: wrap; gap: 4px 10px; }
        .criteria-name { min-width: 0; width: 100%; text-align: start; }
        .bar-val { min-width: 34px; }

        .summary-box, .feedback-box { padding: 1.1rem .9rem; border-radius: 16px; }
        .summary-row { flex-wrap: wrap; gap: .2rem .8rem; }
        .status-chip { white-space: normal; }
        .stats-grid { grid-template-columns: repeat(2, 1fr); gap: .6rem; }
        .stats-card { padding: .9rem .6rem; }
        .stats-num { font-size: 1.5rem; }
        [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
        [data-testid="metric-container"] { padding: .8rem !important; }

        .fig-hint { display: block; }
        .fig-scroll img { min-width: 640px; }
        [data-testid="stMarkdownContainer"] table { display: block; overflow-x: auto; max-width: 100%; }

        /* comfortable touch targets; 16px inputs stop iOS Safari from zooming in on focus */
        .stButton > button { width: 100%; min-height: 46px; padding: .6rem 1rem !important; font-size: .95rem !important; }
        input, textarea, select, [data-baseweb="select"] input { font-size: 16px !important; }

        .intro-logo-ring { width: 130px; height: 130px; margin-bottom: 1.2rem; }
        .intro-logo-inner { width: 108px; height: 108px; font-size: 2.8rem; }
        .intro-isef { font-size: 1.1rem; padding: 0 .8rem; }
        .intro-sub { padding: 0 1.2rem; font-size: .9rem; margin-bottom: 1.6rem; }
        .intro-progress-bar { width: min(260px, 70vw); }
    }

    /* ══ VERY SMALL PHONES (≤ 360px) ═════════════════════════════════════ */
    @media (max-width: 360px) {
        .plant-grid, .stats-grid { grid-template-columns: 1fr; }
        .step-label { font-size: .6rem; max-width: 54px; }
    }

    /* ══ SHORT SCREENS / PHONES IN LANDSCAPE ═════════════════════════════ */
    @media (max-height: 520px) and (orientation: landscape) {
        .intro-overlay { justify-content: flex-start; overflow-y: auto; padding-top: 1rem; }
        .intro-logo-ring { display: none; }
    }

    /* ══ TOUCH: no sticky hover lift after a tap ═════════════════════════ */
    @media (hover: none) {
        .plant-card:hover, .stats-card:hover, .info-pill:hover,
        [data-testid="metric-container"]:hover, .stButton > button:hover {
            transform: none !important;
        }
    }

    /* ══ REDUCED MOTION ══════════════════════════════════════════════════ */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important; animation-iteration-count: 1 !important;
            transition-duration: .01ms !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def creators_html(T):
    """Creator credit line, in the active language."""
    return (
        '<div class="creators">'
        f'<span>{html.escape(T["creators_label"])}</span>'
        f'<span class="creator-name">{html.escape(T["creator_1"])}</span>'
        '<span class="creator-pair">'
        f'{html.escape(T["creators_and"])} '
        f'<span class="creator-name">{html.escape(T["creator_2"])}</span>'
        '</span>'
        '</div>'
    )


def show_figure(fig, alt, T):
    """Show a Matplotlib figure as an image that fills the width on desktop and
    can be swiped sideways on phones (a 14x9 layout squeezed into 360px is unreadable)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    st.markdown(
        f'<div class="fig-hint">{html.escape(T["fig_swipe_hint"])}</div>'
        f'<div class="fig-scroll"><img src="data:image/png;base64,{data}" alt="{html.escape(alt)}"></div>',
        unsafe_allow_html=True,
    )


def plant_cards_html(plants_df, T, lang):
    """All plant cards in one responsive grid (4 columns -> 3 -> 2 -> 1 as the screen narrows)."""
    wi = T['water_icons']
    cards = []
    for _, p in plants_df.iterrows():
        stars = "⭐" * int(p['beauty'])
        name  = p['name_en'] if lang == 'en' else p['name']
        other = p['name_en'] if lang == 'ar' else p['name']
        cards.append(
            '<div class="plant-card">'
            '<div style="font-size:1.6rem">🌿</div>'
            f'<div class="plant-name">{html.escape(str(name))}</div>'
            f'<div class="plant-en">{html.escape(str(other))}</div>'
            f'<div style="margin:.3rem 0">{wi.get(p["water"], "💧")}</div>'
            '<div style="background:rgba(0,230,118,.1);border-radius:6px;'
            'padding:.15rem .4rem;font-size:.78rem;color:#69f0ae">'
            f'{label_use(p["use"], lang)}</div>'
            f'<div style="color:#ffd600;font-size:.88rem">{stars}</div>'
            f'<div class="plant-temp">🌡️ {p["temp_min"]}° — {p["temp_max"]}°C</div>'
            f'<div class="plant-temp">{_label(lang, "Kc تقديري", "Provisional Kc")}: {estimated_landscape_kc(p):.2f}</div>'
            f'<div class="plant-temp">🌳 CO₂: {p.get("co2", 0)} kg/yr</div>'
            '</div>'
        )
    return '<div class="plant-grid">' + ''.join(cards) + '</div>'


# ═══════════════════════════════════════════════════════════════════════════════
# PART 11 — INTRO SCREEN
# ═══════════════════════════════════════════════════════════════════════════════

def show_intro_screen(T):
    """شاشة المقدمة مع زوم إن على اسم المشروع"""
    st.markdown("""
    <div class="intro-overlay" id="introOverlay">
        <div class="intro-particles" id="particles"></div>
        <div class="intro-logo-ring">
            <div class="intro-logo-inner">🌿</div>
        </div>
        <div class="intro-title">حسونة جرين</div>
        <div class="intro-title" style="font-size:clamp(1.2rem,2.5vw,2rem); margin-top:-0.5rem;">
            Hassouna Green
        </div>
        <div class="intro-isef">✦ Sustainable Land Planning ✦</div>
        <div class="intro-sub">
            تخطيط زراعي مستدام يراعي المناخ والمياه والتربة
        </div>
        __CREATORS__
        <div class="intro-progress-bar">
            <div class="intro-progress-inner"></div>
        </div>
        <div style="color:#3a6a4a; font-size:0.85rem; text-align:center;">
            جارٍ تحميل قاعدة بيانات النباتات والمحافظات...
        </div>
    </div>
    """.replace("__CREATORS__",
                creators_html(T).replace('class="creators"', 'class="creators intro-creators"', 1)),
        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 12 — STEP WIZARD COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════

def render_step_wizard(current_step, T, lang):
    steps = [T["step_location"], T["step_land"], T["step_water"], T["step_result"]]
    items = []
    for i, label in enumerate(steps, 1):
        if i < current_step:
            circle_cls = "done"
            conn_cls   = "done-connector"
            lbl_cls    = ""
            icon = "✓"
        elif i == current_step:
            circle_cls = "active"
            conn_cls   = ""
            lbl_cls    = "active-label"
            icon = str(i)
        else:
            circle_cls = "pending"
            conn_cls   = ""
            lbl_cls    = ""
            icon = str(i)

        connector = ""
        if i < len(steps):
            connector = f'<div class="step-connector {conn_cls}"></div>'

        # Keep this HTML on one line: in Markdown, an indented line that follows
        # a blank line is rendered as a code block instead of HTML.
        items.append(
            f'<div class="step-item"><div style="text-align:center">'
            f'<div class="step-circle {circle_cls}">{icon}</div>'
            f'<div class="step-label {lbl_cls}">{html.escape(str(label))}</div>'
            f'</div></div>{connector}'
        )

    st.markdown(
        '<div class="step-wizard">' + ''.join(items) + '</div>',
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 13 — WATER CHART
# ═══════════════════════════════════════════════════════════════════════════════

def render_water_chart(water_data, T):
    fig2, ax2 = plt.subplots(figsize=(10, 4.5))
    fig2.patch.set_facecolor('#080f09')
    ax2.set_facecolor('#0a140a')

    cats  = [T['weekly'], T['monthly'], T['yearly']]
    ai_v  = [water_data['ai_w'],   round(water_data['ai_w'] * WEEKS_PER_MONTH),   water_data['ai_y']]
    tr_v  = [water_data['trad_w'], round(water_data['trad_w'] * WEEKS_PER_MONTH), water_data['trad_y']]
    x     = np.arange(len(cats))
    bw    = 0.35

    bars_trad = ax2.bar(x - bw/2, tr_v, bw,
                        label=T['traditional_label'], color='#ef5350', alpha=0.85, edgecolor='none',
                        zorder=3)
    bars_ai   = ax2.bar(x + bw/2, ai_v, bw,
                        label=T['our_system'],         color='#00e676', alpha=0.85, edgecolor='none',
                        zorder=3)

    ax2.set_xticks(x)
    ax2.set_xticklabels(cats, fontsize=11, color='#b9f6ca', fontfamily='DejaVu Sans')
    ax2.set_ylabel(T['liters'], fontsize=11, color='#69f0ae')
    ax2.tick_params(colors='#69f0ae')
    for sp in ax2.spines.values():
        sp.set_color('#1a3a1d')
    ax2.yaxis.set_tick_params(labelcolor='#69f0ae')
    ax2.set_facecolor('#0a140a')
    ax2.yaxis.grid(True, color='#1a3a1d', linestyle='--', alpha=0.5)
    ax2.set_axisbelow(True)

    ax2.legend(fontsize=10, prop={'family': 'DejaVu Sans'},
               facecolor='#080f09', edgecolor='#1a3a1d', labelcolor='#b9f6ca')

    for b in bars_trad:
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
                 f'{int(b.get_height()):,}', ha='center', va='bottom',
                 fontsize=7.5, color='#ef9a9a')
    for b in bars_ai:
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
                 f'{int(b.get_height()):,}', ha='center', va='bottom',
                 fontsize=7.5, color='#69f0ae')

    plt.tight_layout()
    return fig2


# ═══════════════════════════════════════════════════════════════════════════════

# GULF_AI_UPGRADE_V5 - UAE + QATAR + ADVANCED AGRICULTURAL AI MODULES

def _label(lang, ar, en):
    return ar if lang == "ar" else en


def _unit_code(value):
    """Return 'm' or 'km' for a stored unit (also accepts older translated labels)."""
    return "km" if value in ("km", "km²", "كم", "كم²") else "m"


def _dim_unit_label(code, lang):
    return _label(lang, "كم", "km") if code == "km" else _label(lang, "م", "m")


ET0_SOURCE_AR = {
    "Open-Meteo daily forecast": "توقعات Open-Meteo اليومية",
    "Open-Meteo historical archive": "أرشيف Open-Meteo التاريخي",
    "Open-Meteo five-year monthly climate normal": "متوسط Open-Meteo الشهري لخمس سنوات",
    "ET0 unavailable": "ET₀ غير متاح",
}
ANNUAL_BASIS_AR = {
    "monthly climate normals": "المتوسطات المناخية الشهرية",
    "selected-day annualized estimate": "تقدير سنوي من يوم التصميم",
    "legacy ordinal fallback": "تقدير احتياطي قديم",
}


def _et0_source_label(source, lang):
    return ET0_SOURCE_AR.get(source, source) if lang == "ar" else source


def _annual_basis_label(basis, lang):
    return ANNUAL_BASIS_AR.get(basis, basis) if lang == "ar" else basis


def _open_uploaded_image(uploaded_file, size):
    """Open an uploaded image as RGB, or return None if it is missing or not a readable image."""
    if uploaded_file is None or Image is None:
        return None
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    try:
        return Image.open(uploaded_file).convert("RGB").resize(size)
    except Exception:
        return None

EGYPT = "\u0645\u0635\u0631"
UAE = "\u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a"
QATAR = "\u0642\u0637\u0631"
# Country names, labels and location lists are loaded from the database (PART 2).
EGYPT_LOCATION_KEYS = COUNTRY_LOCATION_KEYS.get(EGYPT, [])
SAND_DESERT="\u0631\u0645\u0644\u064a\u0629 \u0635\u062d\u0631\u0627\u0648\u064a\u0629"; SAND_LIME="\u0631\u0645\u0644\u064a\u0629 \u0643\u0644\u0633\u064a\u0629"; SABKHA="\u0633\u0628\u062e\u064a\u0629 \u0645\u0644\u062d\u064a\u0629"; GRAVEL="\u062d\u0635\u0648\u064a\u0629"; OASIS="\u0637\u064a\u0646\u064a\u0629 \u0648\u0627\u062d\u0627\u062a"; COAST="\u0631\u0645\u0644\u064a\u0629 \u0633\u0627\u062d\u0644\u064a\u0629"; URBAN="\u062a\u0631\u0628\u0629 \u0639\u0645\u0631\u0627\u0646\u064a\u0629 \u0645\u062d\u0633\u0646\u0629"; MOUNTAIN="\u062d\u0635\u0648\u064a\u0629 \u062c\u0628\u0644\u064a\u0629"; LIME="\u0643\u0644\u0633\u064a\u0629"
def get_country_options(lang="ar"):
    return [COUNTRY_LABELS_EN[c] for c in GULF_AI_COUNTRIES] if lang == "en" else GULF_AI_COUNTRIES[:]

def normalize_country(label):
    return {v:k for k,v in COUNTRY_LABELS_EN.items()}.get(label, label)

def get_location_keys_for_country(country):
    return COUNTRY_LOCATION_KEYS.get(normalize_country(country), EGYPT_LOCATION_KEYS)

def get_location_country(location):
    for c, keys in COUNTRY_LOCATION_KEYS.items():
        if location in keys: return c
    return EGYPT

def analyze_satellite_input(uploaded_file, soil, avg_temp, lang="ar"):
    """
    Heuristic, image-based proxy for land suitability — NOT a trained CV/ML
    model. If the user uploads a land/satellite image, we estimate:
      - vegetation greenness from the excess-green index (2G - R - B)
      - brightness from mean pixel intensity
      - dryness as a function of redness, brightness and low greenness
    If no image is provided, we fall back to a temperature-based estimate
    so the dashboard still shows a sensible baseline.
    This should be presented to judges as a transparent color/heuristic
    proxy, not a deep-learning vegetation classifier.
    """
    # Fallback values when no image is uploaded: derive a rough estimate
    # purely from average temperature (hotter => drier baseline assumption).
    vegetation = 0.28
    dryness = min(0.9, max(0.15, (avg_temp - 18) / 30))
    brightness = 0.55

    img = _open_uploaded_image(uploaded_file, (160, 160))
    if img is not None:
        arr = np.array(img).astype(float) / 255.0
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        # Excess Green Index: vegetation tends to reflect more green light.
        excess_green = np.maximum(0, 2 * g - r - b)
        vegetation = float(np.clip(excess_green.mean() * 2.4, 0, 1))

        brightness = float(np.clip(arr.mean(), 0, 1))
        dryness = float(np.clip((r.mean() + brightness - vegetation) / 2, 0, 1))

    # Combine into a single suitability score (0-100). Salt-prone or
    # sandy/desert soils get a suitability penalty; everything else gets
    # a smaller baseline penalty to keep scores realistic.
    soil_penalty = 18 if soil in [SABKHA, SAND_DESERT, SAND_LIME] else 6
    suitability = round(np.clip(
        (1 - dryness) * 45 + vegetation * 25 + 72 - soil_penalty, 0, 100
    ))

    return {
        "vegetation": round(vegetation * 100),
        "dryness": round(dryness * 100),
        "brightness": round(brightness * 100),
        "suitability": suitability,
        "image_error": uploaded_file is not None and img is None,
    }


def calculate_economics(area_sqm, water_data, recommended, country=EGYPT, currency=None, lang="ar"):
    """
    Estimates setup cost, annual irrigation cost, ROI and payback period
    for the recommended planting plan, converted into the requested
    currency (EGP / AED / QAR / USD).

    Cost basis (per m², per year) is a simplified planning estimate, not
    a certified quantity-surveyor budget — useful for comparing design
    choices, not for a real procurement contract.
    """
    currency = currency or {EGYPT: "EGP", UAE: "AED", QATAR: "QAR"}.get(country, "EGP")
    fx_to_local = {"EGP": 1, "AED": 0.075, "QAR": 0.074, "USD": 0.020}.get(currency, 1)

    # Setup cost per m² is higher in UAE/Qatar (higher labor & material costs).
    setup_cost_per_sqm = 155 if country == EGYPT else 560
    setup_cost = round(area_sqm * setup_cost_per_sqm * fx_to_local)

    annual_water_m3 = water_data.get("ai_y", 0) / 1000
    saved_water_m3 = (water_data.get("trad_y", 0) - water_data.get("ai_y", 0)) / 1000
    cost_per_m3 = 7 if country == EGYPT else 28
    irrigation_cost = round(annual_water_m3 * cost_per_m3 * fx_to_local)

    maintenance = round(setup_cost * 0.11)

    # Annual return blends land-value uplift, water savings, and plant value.
    annual_return = round(
        area_sqm * 34 * fx_to_local
        + saved_water_m3 * 22 * fx_to_local
        + len(recommended) * 360 * fx_to_local
    )
    net_profit = annual_return - irrigation_cost - maintenance

    return {
        "currency": currency,
        "setup_cost": setup_cost,
        "irrigation_cost": irrigation_cost,
        "maintenance": maintenance,
        "annual_return": annual_return,
        "net_profit": net_profit,
        "roi": round(net_profit / setup_cost * 100, 1) if setup_cost else 0,
        "payback": round(setup_cost / net_profit, 1) if net_profit > 0 else None,   # None = never pays back
    }


def detect_disease_from_image(uploaded_file, lang="ar"):
    """
    Color-threshold based screening for visible plant stress symptoms —
    NOT a trained disease-classification model. Flags likely fungal
    spotting (high brown-pixel ratio), nutrient/salinity chlorosis (high
    yellow-pixel ratio), or general heat/drought stress, based on simple
    RGB thresholds. Present to judges as an explainable rule-based
    screening tool, a reasonable first step before deep-learning
    classifiers, not a replacement for one.
    """
    if uploaded_file is None or Image is None:
        return {
            "disease": _label(lang, "ارفع صورة نبات", "Upload plant image"),
            "confidence": 0,
            "treatment": "",
        }

    img = _open_uploaded_image(uploaded_file, (180, 180))
    if img is None:
        return {
            "disease": _label(lang, "تعذر قراءة الصورة؛ ارفع ملف PNG أو JPG صالحاً",
                              "The image could not be read; upload a valid PNG or JPG"),
            "confidence": 0,
            "treatment": "",
        }
    arr = np.array(img).astype(float)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    yellow_ratio = float(((r > 110) & (g > 100) & (b < 95)).mean())
    brown_ratio = float(((r > 80) & (g < 120) & (b < 90)).mean())
    green_ratio = float((g > r * 1.08).mean())

    if brown_ratio > 0.22:
        return {
            "disease": _label(lang, "تبقع الأوراق أو إجهاد فطري محتمل", "Possible leaf-spot or fungal stress"),
            "confidence": round(min(96, 58 + brown_ratio * 140)),
            "treatment": _label(
                lang,
                "أزل الأوراق المتضررة وحسّن التهوية، واستشر مختصاً قبل استخدام مبيد.",
                "Remove affected leaves, improve airflow, and consult an expert before using fungicide.",
            ),
        }

    if yellow_ratio > 0.25:
        return {
            "disease": _label(lang, "اصفرار غذائي أو إجهاد ملوحة محتمل", "Possible nutrient chlorosis or salinity stress"),
            "confidence": round(min(94, 55 + yellow_ratio * 120)),
            "treatment": _label(
                lang,
                "افحص الملوحة ودرجة الحموضة والعناصر قبل إضافة أي مغذٍ.",
                "Check salinity, pH and nutrients before applying amendments.",
            ),
        }

    looks_healthy = green_ratio > 0.35
    return {
        "disease": _label(
            lang,
            "يبدو النبات سليماً" if looks_healthy else "إجهاد حراري أو جفاف محتمل",
            "Plant looks healthy" if looks_healthy else "Possible heat or drought stress",
        ),
        "confidence": round(70 + min(green_ratio, 0.4) * 50),
        "treatment": _label(
            lang,
            "حافظ على الري المناسب والغطاء العضوي والمتابعة المنتظمة.",
            "Maintain appropriate irrigation, mulch and regular monitoring.",
        ),
    }


def calculate_carbon_footprint(recommended, area_sqm, water_data):
    """
    Estimates yearly CO2 impact of the recommended planting plan:
      - direct carbon absorption from the recommended plants' co2 ratings,
        scaled by planted area
      - an indirect water-energy saving credit, since pumping/treating
        less irrigation water also saves energy-related emissions
    Expressed in kg CO2/year, plus a "tree equivalent" using a standard
    rough estimate of ~21 kg CO2/year absorbed by one mature tree.
    """
    if len(recommended):
        absorbed = round(float(recommended.get("co2", pd.Series(dtype=float)).sum()) * max(1, area_sqm / 100))
    else:
        absorbed = 0

    water_saved_m3 = max(0, (water_data.get("trad_y", 0) - water_data.get("ai_y", 0)) / 1000)
    water_energy_co2 = round(water_saved_m3 * 0.34, 1)  # kg CO2 saved per m3 of water not pumped/treated

    total = round(absorbed + water_energy_co2, 1)
    return {
        "absorbed": absorbed,
        "water_energy": water_energy_co2,
        "total": total,
        "trees_equiv": round(total / 21, 1),
    }


def assistant_answer(q, country, gov, region, soil, temp, water, lang="ar"):
    """Small keyword-matched FAQ helper; this is not an open-ended language model."""
    country, gov, soil = label_country(country, lang), label_location(gov, lang), label_soil(soil, lang)
    q = (q or "").lower()
    words = set(re.findall(r"\w+", q))

    def has(*terms):
        # Short terms must be whole words; longer ones may appear inside a word (e.g. "الزيتون").
        return any(t in words or (len(t) > 3 and t in q) for t in terms)

    if has("olive", "olives", "زيتون"):
        return _label(lang,
            f"يمكن أن تنجح شجرة الزيتون في {gov} إذا تم التحكم في الملوحة. التربة: {soil}، الحرارة: {temp}°م. يُفضّل الري بالتنقيط وإضافة غطاء عضوي.",
            f"Olive may suit {gov} if salinity is managed. Soil: {soil}; temperature: {temp}°C. Prefer drip irrigation and mulch.")
    if has("salt", "salty", "saline", "salinity", "ملوحة", "ملح", "مالحة", "مالح"):
        return _label(lang,
            "اختر نباتات متحملة للملوحة مثل الأثل والقطف والسدر، مع صرف جيد وغسيل محسوب للتربة.",
            "Consider salt-tolerant plants such as tamarix, saltbush and sidr, with good drainage and planned leaching.")
    if has("water", "watering", "irrigation", "irrigate", "ري", "الري", "بالري", "للري", "سقي", "السقي", "مياه", "ماء"):
        return _label(lang,
            f"عند حرارة {temp}°م، استخدم الري بالتنقيط صباحاً وغطاءً عضوياً، وتحقق من رطوبة منطقة الجذور.",
            f"At {temp}°C, use morning drip irrigation and mulch, and check root-zone moisture.")
    return _label(lang,
        f"لـ {country}/{gov}: ابدأ بالنباتات الملائمة للتربة والمناخ، ثم تحقق من جودة مياه الري والصرف.",
        f"For {country}/{gov}, start with plants suited to the soil and climate, then verify irrigation-water quality and drainage.")


def render_advanced_intelligence_suite(lang, country, gov, region, soil, temp, area, water_budget, water_data, recommended):
    """Render practical tools and state clearly when outputs are heuristic estimates."""
    st.markdown("---")
    st.markdown(_label(lang, "### أدوات التخطيط الزراعي", "### Agricultural Planning Tools"))
    tabs = st.tabs([
        _label(lang, "تحليل صورة الأرض", "Land-image proxy"),
        _label(lang, "تقدير اقتصادي", "Economic estimate"),
        _label(lang, "فحص إجهاد النبات", "Plant stress screening"),
        _label(lang, "تقدير الكربون", "Carbon estimate"),
        _label(lang, "أسئلة زراعية", "Agricultural FAQ"),
    ])

    with tabs[0]:
        uploaded_image = st.file_uploader(_label(lang, "صورة أرض / قمر صناعي", "Land / satellite image"), type=["png", "jpg", "jpeg"], key="sat_upload")
        sat = analyze_satellite_input(uploaded_image, soil, temp, lang)
        if sat.get("image_error"):
            st.warning(_label(lang,
                "تعذر قراءة الصورة؛ ارفع ملف PNG أو JPG صالحاً. القيم التالية تقدير بدون صورة.",
                "The image could not be read; upload a valid PNG or JPG. The values below are the no-image estimate."))
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(_label(lang, "ملاءمة تقديرية", "Heuristic suitability"), f"{sat['suitability']}%")
        m2.metric(_label(lang, "اخضرار الصورة", "Image greenness"), f"{sat['vegetation']}%")
        m3.metric(_label(lang, "مؤشر الجفاف", "Dryness proxy"), f"{sat['dryness']}%")
        m4.metric(_label(lang, "سطوع الصورة", "Image brightness"), f"{sat['brightness']}%")
        st.caption(_label(lang,
            "هذا تقدير لوني مبسط للصورة، وليس تحليلاً طيفياً أو نموذجاً مدرباً للاستشعار عن بعد.",
            "This is a simple image-color proxy, not spectral satellite analysis or a trained remote-sensing model."))

    with tabs[1]:
        default_currency = {EGYPT: "EGP", UAE: "AED", QATAR: "QAR"}.get(country, "EGP")
        selected_currency = st.selectbox(_label(lang, "العملة", "Currency"), list(dict.fromkeys([default_currency, "EGP", "AED", "QAR", "USD"])), key="eco_cur")
        eco = calculate_economics(area, water_data, recommended, country, selected_currency, lang)
        e1, e2, e3, e4 = st.columns(4)
        e1.metric(_label(lang, "تكلفة تأسيس تقديرية", "Estimated setup cost"), f"{eco['setup_cost']:,} {eco['currency']}")
        e2.metric(_label(lang, "ري سنوي تقديري", "Estimated annual irrigation"), f"{eco['irrigation_cost']:,} {eco['currency']}")
        e3.metric("ROI", f"{eco['roi']}%")
        e4.metric(_label(lang, "فترة استرداد تقديرية", "Estimated payback"),
                  f"{eco['payback']} {_label(lang, 'سنة', 'yr')}" if eco['payback'] is not None
                  else _label(lang, "لا يوجد استرداد", "No payback"))
        st.caption(_label(lang, "مؤشرات تخطيطية مبسطة وليست عرض سعر أو دراسة جدوى معتمدة.", "Simplified planning estimates, not a contractor quote or certified feasibility study."))

    with tabs[2]:
        uploaded_leaf = st.file_uploader(_label(lang, "ارفع صورة نبات", "Upload plant image"), type=["png", "jpg", "jpeg"], key="disease_upload")
        diagnosis = detect_disease_from_image(uploaded_leaf, lang)
        st.metric(_label(lang, "درجة المؤشر القاعدي", "Heuristic indicator score"), f"{diagnosis['confidence']}/100")
        st.info(diagnosis['disease'] + (f" — {diagnosis['treatment']}" if diagnosis['treatment'] else ""))
        st.caption(_label(lang, "فحص لوني أولي وليس تشخيصاً نباتياً أو نموذج كشف أمراض مدرباً.", "Color-threshold screening only; not a plant diagnosis or trained disease classifier."))

    with tabs[3]:
        carbon = calculate_carbon_footprint(recommended, area, water_data)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(_label(lang, "امتصاص نباتي تقديري", "Estimated plant uptake"), f"{carbon['absorbed']:,} kg CO₂/yr")
        c2.metric(_label(lang, "وفر طاقة المياه", "Water-energy credit"), f"{carbon['water_energy']:,} kg CO₂")
        c3.metric(_label(lang, "الأثر التقديري", "Estimated total"), f"{carbon['total']:,} kg CO₂/yr")
        c4.metric(_label(lang, "مكافئ أشجار تقريبي", "Approx. tree equivalent"), f"{carbon['trees_equiv']:,}")
        st.caption(_label(lang, "تقدير تقريبي يعتمد على معاملات قاعدة النباتات، وليس قياساً للكربون.", "Approximate catalog-based estimate; this is not a measured carbon balance."))

    with tabs[4]:
        if "agri_chat" not in st.session_state:
            st.session_state.agri_chat = []
        question = st.text_input(_label(lang, "اسأل المساعد الزراعي", "Ask the agricultural FAQ"), placeholder=_label(lang, "هل الزيتون مناسب في أبوظبي؟", "Is olive suitable in Abu Dhabi?"), key="agri_q")
        if st.button(_label(lang, "إرسال", "Send"), key="agri_send") and question:
            answer = assistant_answer(question, country, gov, region, soil, temp, water_budget, lang)
            st.session_state.agri_chat.append((question, answer))
        for asked, answered in st.session_state.agri_chat[-5:]:
            # Escape user-controlled content before embedding it in HTML.
            safe_question = html.escape(str(asked))
            safe_answer = html.escape(str(answered))
            st.markdown(
                f"<div class='summary-box'><b>Q: {safe_question}</b><br>"
                f"<span style='color:#b9f6ca'>{safe_answer}</span></div>",
                unsafe_allow_html=True,
            )


# PART 14 — MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

# IRRIGATION_WATER_SUITABILITY_FROM_PDF - based on uploaded water suitability PDF

def classify_irrigation_water(ec_us_cm, sar, rsc, chloride_meq, sulfate_meq, boron_mg_l, soil, lang="en"):
    """Rule-based screening from entered chemistry; verify thresholds locally."""
    tds_ppm = round(ec_us_cm * 0.64)
    if ec_us_cm < 250:
        salinity_en, salinity_ar, salinity_risk = "Low salinity water", "مياه منخفضة الملوحة", 5
        salinity_note_en, salinity_note_ar = "Suitable for many crops with small leaching needs.", "مناسبة لكثير من المحاصيل مع احتياجات غسل محدودة."
    elif ec_us_cm <= 750:
        salinity_en, salinity_ar, salinity_risk = "Medium salinity water", "مياه متوسطة الملوحة", 18
        salinity_note_en, salinity_note_ar = "Avoid highly salt-sensitive plants and maintain drainage.", "تجنب النباتات شديدة الحساسية للملوحة وحافظ على الصرف."
    elif ec_us_cm <= 2250:
        salinity_en, salinity_ar, salinity_risk = "High salinity water", "مياه عالية الملوحة", 38
        salinity_note_en, salinity_note_ar = "Use tolerant plants, good drainage and planned leaching.", "استخدم نباتات متحملة مع صرف جيد وغسيل محسوب."
    else:
        salinity_en, salinity_ar, salinity_risk = "Very high salinity water", "مياه عالية الملوحة جداً", 58
        salinity_note_en, salinity_note_ar = "Requires blending, drainage and tolerant crops; seek expert review.", "تتطلب خلطاً وصرفاً ونباتات متحملة؛ استشر مختصاً."

    if sar < 10:
        sar_en, sar_ar, sar_risk = "Low sodium hazard", "خطر صوديوم منخفض", 5
        sar_note_en, sar_note_ar = "Generally low sodium hazard.", "خطر الصوديوم منخفض عموماً."
    elif sar < 18:
        sar_en, sar_ar, sar_risk = "Medium sodium hazard", "خطر صوديوم متوسط", 20
        sar_note_en, sar_note_ar = "Check soil texture and crop sensitivity.", "تحقق من قوام التربة وحساسية المحصول."
    elif sar < 26:
        sar_en, sar_ar, sar_risk = "High sodium hazard", "خطر صوديوم مرتفع", 38
        sar_note_en, sar_note_ar = "Consider drainage and calcium amendment after expert review.", "قد يلزم الصرف ومصدر كالسيوم بعد مراجعة مختص."
    else:
        sar_en, sar_ar, sar_risk = "Very high sodium hazard", "خطر صوديوم مرتفع جداً", 55
        sar_note_en, sar_note_ar = "Water blending and soil-management review are advised.", "يوصى بخلط المياه ومراجعة إدارة التربة."

    if rsc < 1.25:
        rsc_en, rsc_ar, rsc_risk = "Suitable RSC", "RSC مناسب", 4
        rsc_note_en, rsc_note_ar = "Residual sodium carbonate is within the lower screening band.", "كربونات الصوديوم المتبقية ضمن نطاق الفحص الأقل."
    elif rsc <= 2.5:
        rsc_en, rsc_ar, rsc_risk = "Marginal RSC", "RSC هامشي", 22
        rsc_note_en, rsc_note_ar = "Monitor soil structure and confirm with lab analysis.", "راقب بنية التربة وأكد النتيجة بتحليل مخبري."
    else:
        rsc_en, rsc_ar, rsc_risk = "Unsuitable RSC", "RSC غير مناسب", 45
        rsc_note_en, rsc_note_ar = "High carbonate risk; confirm treatment requirements with an expert.", "خطر كربونات مرتفع؛ أكد المعالجة المطلوبة مع مختص."

    chloride_risk = 5 if chloride_meq < 4 else 18 if chloride_meq <= 10 else 34
    sulfate_risk = 4 if sulfate_meq < 10 else 14 if sulfate_meq <= 20 else 26
    boron_risk = 4 if boron_mg_l < 0.7 else 18 if boron_mg_l <= 3 else 36
    soil_extra = 10 if soil in ["طينية", "طينية نيلية", "طينية ساحلية", "طينية واحات"] and sar >= 18 else 0
    risk = min(100, round(salinity_risk + sar_risk + rsc_risk + chloride_risk + sulfate_risk + boron_risk + soil_extra))
    suitability = max(0, 100 - risk)
    if suitability >= 75:
        final_en, final_ar = "Good screening result", "نتيجة فحص جيدة"
    elif suitability >= 55:
        final_en, final_ar = "Use with management", "تتطلب إدارة مناسبة"
    elif suitability >= 35:
        final_en, final_ar = "Marginal — needs treatment review", "هامشية — تحتاج مراجعة المعالجة"
    else:
        final_en, final_ar = "High risk — expert review required", "مخاطر مرتفعة — تلزم مراجعة مختص"
    ar = lang == "ar"
    return {
        "tds_ppm": tds_ppm, "suitability": suitability,
        "final_class": final_ar if ar else final_en,
        "salinity_class": salinity_ar if ar else salinity_en,
        "salinity_note": salinity_note_ar if ar else salinity_note_en,
        "sar_class": sar_ar if ar else sar_en, "sar_note": sar_note_ar if ar else sar_note_en,
        "rsc_class": rsc_ar if ar else rsc_en, "rsc_note": rsc_note_ar if ar else rsc_note_en,
        "chloride_risk": chloride_risk, "sulfate_risk": sulfate_risk,
        "boron_risk": boron_risk, "risk": risk,
    }


def render_irrigation_water_suitability(lang, soil, water_data):
    st.markdown("---")
    st.markdown(_label(lang, "### ملاءمة مياه الري — فحص إرشادي", "### Irrigation Water Suitability — Screening"))
    with st.expander(_label(lang, "إدخال كيمياء المياه", "Enter water chemistry"), expanded=True):
        st.caption(_label(lang,
            "فحص قاعدي أولي يعتمد على المدخلات والحدود المبرمجة؛ لا يغني عن تحليل مخبري أو مراجعة محلية.",
            "Preliminary rule-based screening from entered values; not a substitute for laboratory testing or local standards."))
        c1, c2, c3 = st.columns(3)
        ec_us = c1.number_input("EC (µS/cm)", min_value=0.0, value=750.0, step=50.0, key="water_ec_us")
        target_root_ec = c2.number_input(_label(lang, "EC المستهدف لمنطقة الجذور (µS/cm)", "Target root-zone EC (µS/cm)"), min_value=1.0, value=4000.0, step=100.0, key="water_root_ec")
        base_irrigation_m3 = c3.number_input(_label(lang, "الري الأساسي لكل دورة (م³)", "Base irrigation per cycle (m³)"), min_value=0.0, value=max(1.0, round(water_data.get("ai_w", 1000) / 1000, 1)), step=0.5, key="water_base_m3")
        a1, a2, a3 = st.columns(3)
        sodium = a1.number_input("Na+ (meq/L)", min_value=0.0, value=6.0, step=0.1, key="water_na")
        calcium = a2.number_input("Ca++ (meq/L)", min_value=0.0, value=4.0, step=0.1, key="water_ca")
        magnesium = a3.number_input("Mg++ (meq/L)", min_value=0.0, value=2.0, step=0.1, key="water_mg")
        b1, b2, b3, b4, b5 = st.columns(5)
        carbonate = b1.number_input("CO3 (meq/L)", min_value=0.0, value=0.2, step=0.1, key="water_co3")
        bicarbonate = b2.number_input("HCO3 (meq/L)", min_value=0.0, value=3.0, step=0.1, key="water_hco3")
        chloride = b3.number_input("Cl- (meq/L)", min_value=0.0, value=4.0, step=0.1, key="water_cl")
        sulfate = b4.number_input("SO4 (meq/L)", min_value=0.0, value=8.0, step=0.1, key="water_so4")
        boron = b5.number_input(_label(lang, "البورون (mg/L)", "Boron (mg/L)"), min_value=0.0, value=0.5, step=0.1, key="water_boron")
        sar = sodium / math.sqrt(max((calcium + magnesium) / 2, 0.0001))
        rsc = (carbonate + bicarbonate) - (calcium + magnesium)
        # Leaching requirement LR = ECw / ECtarget; applied water = base / (1 - LR) (FAO-29).
        lr = ec_us / target_root_ec if target_root_ec else 0.0
        lr_pct = lr * 100
        total_irrigation_m3 = base_irrigation_m3 / (1 - lr) if lr < 1 else None
        res = classify_irrigation_water(ec_us, sar, rsc, chloride, sulfate, boron, soil, lang)
        if lr >= 1:
            st.warning(_label(lang,
                "EC مياه الري يساوي أو يتجاوز EC المستهدف لمنطقة الجذور؛ لا يمكن للغسيل وحده الوصول لهذا الهدف. "
                "استخدم مياهاً أقل ملوحة أو هدفاً أعلى لنباتات متحملة.",
                "Irrigation-water EC is at or above the target root-zone EC, so leaching alone cannot reach this "
                "target. Use less saline water or a higher target for tolerant plants."))
        if calcium + magnesium <= 0 and sodium > 0:
            st.warning(_label(lang,
                "يحتاج حساب SAR إلى قيم Ca و Mg؛ عندما تكون الاثنتان صفراً تكون قيمة SAR غير محددة فعلياً.",
                "SAR needs Ca and Mg values; with both at zero the SAR is effectively undefined."))
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(_label(lang, "ملاءمة الفحص", "Screening suitability"), f"{res['suitability']}%")
        m2.metric("TDS", f"{res['tds_ppm']:,} ppm")
        m3.metric("SAR", f"{sar:.2f}")
        m4.metric("RSC", f"{rsc:.2f} meq/L")
        l1, l2, l3 = st.columns(3)
        l1.metric(_label(lang, "متطلب الغسيل التقريبي", "Approx. leaching ratio"), f"{lr_pct:.1f}%")
        l2.metric(_label(lang, "ري بعد الغسيل", "Irrigation after leaching"),
                  f"{total_irrigation_m3:,.1f} m³" if total_irrigation_m3 is not None else "—")
        l3.metric(_label(lang, "مياه إضافية", "Additional water"),
                  f"{total_irrigation_m3 - base_irrigation_m3:,.1f} m³" if total_irrigation_m3 is not None else "—")
        recommendation = _label(lang,
            "استخدم الري بالتنقيط والصرف والغسيل المخطط، واطلب تحليلاً مخبرياً قبل المعالجة.",
            "Use drip irrigation, drainage and planned leaching; obtain a laboratory analysis before treatment.")
        st.markdown(f"""
        <div class="summary-box">
            <div class="summary-row"><span>{_label(lang, 'النتيجة', 'Overall')}</span><b>{res['final_class']}</b></div>
            <div class="summary-row"><span>{_label(lang, 'الملوحة', 'Salinity')}</span><b>{res['salinity_class']} — {res['salinity_note']}</b></div>
            <div class="summary-row"><span>{_label(lang, 'الصوديوم SAR', 'Sodium SAR')}</span><b>{res['sar_class']} — {res['sar_note']}</b></div>
            <div class="summary-row"><span>RSC</span><b>{res['rsc_class']} — {res['rsc_note']}</b></div>
            <div class="summary-row"><span>{_label(lang, 'تنبيه', 'Note')}</span><b>{recommendation}</b></div>
        </div>
        """, unsafe_allow_html=True)


SHOW_SIDEBAR = False   # quick-stats sidebar (see main())


def main():
    st.set_page_config(
        page_title="Hassouna Green — Sustainable Land Planning",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()

    # ── Session State ──────────────────────────────────────────────────────
    if 'intro_done'   not in st.session_state: st.session_state.intro_done   = False
    if 'form_step'    not in st.session_state: st.session_state.form_step    = 1
    if 'form_data'    not in st.session_state: st.session_state.form_data    = {}
    if 'results_done' not in st.session_state: st.session_state.results_done = False
    if 'lang'         not in st.session_state: st.session_state.lang         = "ar"

    # The intro is shown once per session, as an overlay that fades out by itself.
    show_intro = not st.session_state.intro_done
    st.session_state.intro_done = True

    # ── Language (main screen) ─────────────────────────────────────────────
    # A single control at the top of the main page sets st.session_state.lang.
    lang_codes = ["ar", "en"]
    st.session_state.lang = st.radio(
        "🌐 اللغة / Language",
        lang_codes,
        index=lang_codes.index(st.session_state.lang),
        format_func=lambda code: "العربية" if code == "ar" else "English",
        horizontal=True,
        key="lang_choice",
    )

    # The sidebar is off by default. Its open button lives in the Streamlit header, which this app
    # hides, so nobody could open it - and in Arabic (right-to-left) a collapsed sidebar can leave a
    # stray line on screen. Set SHOW_SIDEBAR = True above main() to bring it back.
    if SHOW_SIDEBAR:
        with st.sidebar:
            # Quick stats sidebar
            df_stats = get_plants_database()
            T_s = TRANSLATIONS[st.session_state.lang]
            st.markdown(f"**{T_s['stats_title']}**")
            st.metric(T_s['total_plants_db'],   len(df_stats))
            st.metric(_label(st.session_state.lang, '\u0627\u0644\u062f\u0648\u0644 / \u0627\u0644\u0645\u0648\u0627\u0642\u0639', 'Countries / locations'), f'{len(COUNTRY_LOCATION_KEYS)} / {len(GOVERNORATE_DATA)}')
            st.metric(T_s['soil_types_count'],   len(ALL_SOIL_TYPES))
            st.caption(_label(st.session_state.lang,
                "التقييم القاعدي بأوزان مبرمجة شفافة؛ دقة حَكَم تعلّم الآلة مقاسة بتحقق متقاطع مكاني (AUC) ومعروضة في صفحة النتائج.",
                "The rule-based score uses transparent programmed weights; the ML judge's accuracy is measured by spatial "
                "cross-validation (AUC) and shown on the results page."))
    else:
        st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],"
                    "[data-testid='collapsedControl']{display:none!important}</style>",
                    unsafe_allow_html=True)

    lang = st.session_state.lang
    T    = TRANSLATIONS[lang]
    ui_dir = 'rtl' if lang == 'ar' else 'ltr'
    ui_align = 'right' if lang == 'ar' else 'left'
    st.markdown(f"<style>.stApp,.main,.form-card,.summary-box,.judge-card,.plant-card,.status-bar,.saving-banner{{direction:{ui_dir}!important;text-align:{ui_align}!important;unicode-bidi:plaintext}} div[data-testid='stTabs'] button{{font-weight:800}}</style>", unsafe_allow_html=True)

    # ── INTRO SCREEN ───────────────────────────────────────────────────────
    # A fixed overlay on top of the page. The page below is already rendered, and
    # the overlay fades out on its own after about 3.5 seconds (CSS animation).
    if show_intro:
        show_intro_screen(T)

    # ── HEADER ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="main-header">
        <h1>{T['app_title']}</h1>
        <p>{T['app_subtitle']}</p>
        <div>
            <span class="isef-badge">{T['brand_badge']}</span>
        </div>
        {creators_html(T)}
    </div>
    """, unsafe_allow_html=True)

    # ── STEP WIZARD ────────────────────────────────────────────────────────
    current_step = st.session_state.form_step if not st.session_state.results_done else 4
    render_step_wizard(current_step, T, lang)

    # ══════════════════════════════════════════════════════════════════════
    # STEP 1 — الموقع والتاريخ
    # ══════════════════════════════════════════════════════════════════════
    if st.session_state.form_step == 1 and not st.session_state.results_done:
        st.markdown(f'<div class="form-card"><div class="form-card-title">{T["form_title_1"]}</div>', unsafe_allow_html=True)

        today = datetime.date.today()
        country_options = get_country_options(lang)
        saved_country = st.session_state.form_data.get('country', EGYPT)
        saved_country_label = COUNTRY_LABELS_EN.get(saved_country, saved_country) if lang == 'en' else saved_country
        if saved_country_label not in country_options: saved_country_label = country_options[0]
        col0, col1, col2 = st.columns(3)
        with col0:
            country_label = st.selectbox(_label(lang, '\U0001f30d \u0627\u0644\u0628\u0644\u062f', 'Country'), country_options, index=country_options.index(saved_country_label), key='country_sel')
            country = normalize_country(country_label)
        gov_list = get_location_keys_for_country(country)
        with col1:
            saved_gov = st.session_state.form_data.get('governorate', gov_list[0])
            if saved_gov not in gov_list: saved_gov = gov_list[0]
            governorate = st.selectbox(f"{T['governorate']}", gov_list, index=gov_list.index(saved_gov), key="gov_sel",
                                       format_func=lambda k: label_location(k, lang))
        with col2:
            gov_data = GOVERNORATE_DATA[governorate]
            regions  = gov_data["regions"]
            default_region = st.session_state.form_data.get('region', regions[0])
            if default_region not in regions: default_region = regions[0]
            region = st.selectbox(f"{T['region']}", regions, index=regions.index(default_region), key="reg_sel",
                                  format_func=lambda r: label_region(governorate, r, lang))

        # عرض وصف المحافظة
        gov_desc = gov_data.get('desc_ar' if lang == 'ar' else 'desc_en', '')
        if gov_desc:
            st.markdown(f'<div class="info-pill">📌 {gov_desc}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**📅 {T['date_label']}**")
        d1, d2, d3 = st.columns(3)
        day   = d1.number_input(T['day'],   1,  31, st.session_state.form_data.get('day',   today.day),   step=1)
        month = d2.number_input(T['month'], 1,  12, st.session_state.form_data.get('month', today.month), step=1)
        year_min, year_max = min(2020, today.year), max(2030, today.year + 5)
        saved_year = int(st.session_state.form_data.get('year', today.year))
        year  = d3.number_input(T['year'],  year_min, year_max, min(max(saved_year, year_min), year_max),  step=1)
        day = min(int(day), calendar.monthrange(int(year), int(month))[1])
        # Remember the entries on every run, so switching language before "Next" keeps them.
        st.session_state.form_data.update({'country': country, 'governorate': governorate, 'region': region,
                                           'day': day, 'month': month, 'year': year})

        season_str, season_type = get_season(month, lang)
        base_temp  = get_temp(governorate, month)
        month_name = T['months'][month]

        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.markdown(f'<div class="info-pill">🗓️ {month_name} {year}</div>', unsafe_allow_html=True)
        col_s2.markdown(f'<div class="info-pill">{season_str}</div>', unsafe_allow_html=True)
        col_s3.markdown(f'<div class="info-pill">🌡️ ~{base_temp}°C {T["est_temp"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        _, btn_col = st.columns([3, 1])
        with btn_col:
            if st.button(T['next'], key="step1_next", width="stretch"):
                st.session_state.form_data.update({
                    'country': country, 'governorate': governorate, 'region': region,
                    'day': day, 'month': month, 'year': year,
                    'season_str': season_str, 'season_type': season_type,
                    'base_temp': base_temp, 'month_name': month_name,
                })
                st.session_state.form_step = 2
                st.rerun()
    # ══════════════════════════════════════════════════════════════════════
    # STEP 2 — بيانات الأرض
    # ══════════════════════════════════════════════════════════════════════
    elif st.session_state.form_step == 2 and not st.session_state.results_done:
        fd = st.session_state.form_data
        gov_data   = GOVERNORATE_DATA[fd['governorate']]
        def_soil   = gov_data["region_soils"].get(fd['region'], gov_data["soil_types"][0])
        soil_opts  = gov_data["soil_types"]
        if def_soil not in soil_opts:
            soil_opts = [def_soil] + soil_opts

        st.markdown(f'<div class="form-card"><div class="form-card-title">{T["form_title_2"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-pill">💡 {T["soil_note"]} — <b>{label_soil(def_soil, lang)}</b></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        col_s, col_u = st.columns(2)
        with col_s:
            saved_soil = st.session_state.form_data.get('soil', def_soil)
            if saved_soil not in soil_opts:
                saved_soil = def_soil
            soil = st.selectbox(f"🪨 {T['soil']}", soil_opts,
                                index=soil_opts.index(saved_soil), key="soil_sel",
                                format_func=lambda k: label_soil(k, lang))
        with col_u:
            # A language-independent code, so switching language keeps the choice.
            unit_opts  = ["m", "km"]
            saved_unit = _unit_code(st.session_state.form_data.get('unit', "m"))
            unit_opt = st.selectbox(f"📐 {T['area_unit']}", unit_opts,
                                    index=unit_opts.index(saved_unit), key="unit_sel",
                                    format_func=lambda u: T['meters'] if u == "m" else T['km'])
        col_w, col_h = st.columns(2)
        width_label = T['width'] if unit_opt == "m" else _label(lang, "العرض (كم)", "Width (km)")
        height_label = T['height'] if unit_opt == "m" else _label(lang, "الطول (كم)", "Length (km)")
        w_val = col_w.number_input(width_label, min_value=0.1,
                                   value=float(st.session_state.form_data.get('w_val', 10.0)),
                                   step=0.5, key="width_in")
        h_val = col_h.number_input(height_label, min_value=0.1,
                                   value=float(st.session_state.form_data.get('h_val', 10.0)),
                                   step=0.5, key="height_in")
        area_sqm = w_val * h_val
        if unit_opt == "km":
            area_sqm_display = area_sqm * 1_000_000
        else:
            area_sqm_display = area_sqm
        st.session_state.form_data.update({'soil': soil, 'unit': unit_opt, 'w_val': w_val, 'h_val': h_val,
                                           'area_sqm': area_sqm_display})
        st.markdown(f'<div class="info-pill">📐 {T["area_total"]}: <b>{area_sqm_display:,.1f} m²</b></div>',
                    unsafe_allow_html=True)
        # soil info chips (bilingual, from the soil_traits table)
        traits = SOIL_TRAITS.get(soil, [])
        if traits:
            chips_html = ''.join(f'<span class="info-pill">{t[lang]}</span>' for t in traits)
            st.markdown(chips_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button(T['prev'], key="step2_prev", width="stretch"):
                st.session_state.form_step = 1
                st.rerun()
        with col_b2:
            if st.button(T['next'], key="step2_next", width="stretch"):
                st.session_state.form_data.update({
                    'soil': soil, 'unit': unit_opt,
                    'w_val': w_val, 'h_val': h_val,
                    'area_sqm': area_sqm_display,
                })
                st.session_state.form_step = 3
                st.rerun()
    # ══════════════════════════════════════════════════════════════════════
    # STEP 3 — الري والمياه
    # ══════════════════════════════════════════════════════════════════════
    elif st.session_state.form_step == 3 and not st.session_state.results_done:
        st.markdown(f'<div class="form-card"><div class="form-card-title">{T["form_title_3"]}</div>', unsafe_allow_html=True)
        water_budget = st.slider(
            f"💧 {T['water_budget']}", 1, 3,
            st.session_state.form_data.get('water_budget', 2),
            help=_label(lang, "1 = منخفض جداً | 2 = متوسط | 3 = عالٍ", "1 = very low | 2 = medium | 3 = high"),
            key="water_slider"
        )
        st.session_state.form_data['water_budget'] = water_budget
        wl_map  = {1: T['water_low'], 2: T['water_mid'], 3: T['water_high']}
        desc_map = {
            1: ("💧", "نباتات جفافية ومتحملة للجفاف — توفير مياه أقصى",
                    "Drought-tolerant plants — maximum water saving"),
            2: ("💧💧", "توازن بين التنوع والاستهلاك المعتدل",
                    "Balance between diversity and moderate consumption"),
            3: ("💧💧💧", "نباتات متنوعة وزاهية — مناسب لمصادر المياه الوفيرة",
                    "Diverse lush plants — suitable for abundant water sources"),
        }
        icon, desc_ar, desc_en = desc_map[water_budget]
        desc = desc_ar if lang == 'ar' else desc_en
        st.markdown(f"""
        <div style="text-align:center; margin: 1rem 0;">
            <div style="font-size:2.5rem; margin-bottom:.5rem">{icon}</div>
            <div class="info-pill">{wl_map[water_budget]}</div>
            <div style="color:#81c784; font-size:.9rem; margin-top:.5rem">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

        st.info(_label(lang,
            "فئة ميزانية المياه تُستخدم لتصفية النباتات فقط. سيُحسب حجم الري بعد اختيار الموقع ومزيج النباتات باستخدام ET₀ ومعامل مجموعة نباتية تقديري.",
            "The water-budget tier filters plant options only. Irrigation volume is calculated after site and plant selection from ET₀ and a provisional functional-group Kc."))

        st.markdown('</div>', unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button(T['prev'], key="step3_prev", width="stretch"):
                st.session_state.form_step = 2
                st.rerun()
        with col_b2:
            if st.button(T['generate'], key="step3_gen", width="stretch", type="primary"):
                st.session_state.form_data['water_budget'] = water_budget
                st.session_state.results_done = True
                st.session_state.form_step    = 4
                st.rerun()
    # ══════════════════════════════════════════════════════════════════════
    # STEP 4 — RESULTS
    # ══════════════════════════════════════════════════════════════════════
    elif st.session_state.results_done:
        fd = st.session_state.form_data
        country      = fd.get('country', get_location_country(fd.get('governorate', 'القاهرة')))
        governorate  = fd.get('governorate', 'القاهرة')
        region       = fd.get('region',       'مدينة نصر')
        month        = fd.get('month',         datetime.date.today().month)
        year         = fd.get('year',          datetime.date.today().year)
        day          = fd.get('day',           datetime.date.today().day)
        # Recomputed here so that switching language also updates these labels.
        season_str, season_type = get_season(int(month), lang)
        month_name   = T['months'][int(month)]
        soil         = fd.get('soil',          'طمييه')
        w_val        = fd.get('w_val',         10.0)
        h_val        = fd.get('h_val',         10.0)
        area_sqm     = fd.get('area_sqm',      100.0)
        unit_opt     = _unit_code(fd.get('unit', "m"))
        dim_unit     = _dim_unit_label(unit_opt, lang)
        water_budget = fd.get('water_budget',   2)

        # Weather for the selected design date; ET₀ is retrieved from Open-Meteo.
        base_temp = get_temp(governorate, month)
        design_date = datetime.date(int(year), int(month), int(day))
        weather = fetch_et0_weather(governorate, design_date)
        avg_temp = weather.get("temperature_c")
        if avg_temp is None:
            avg_temp = base_temp
        et0_for_day = weather.get("et0_mm_day")
        if et0_for_day is None:
            et0_for_day = weather.get("monthly_et0", {}).get(month)

        # ── Core Logic ──────────────────────────────────────────────────────
        df          = get_plants_database()
        recommended = recommend_plants(df, water_budget, soil, avg_temp, top_n=8)
        water_data  = calc_water(recommended, area_sqm, et0_for_day,
                                 weather.get("monthly_et0"), target_year=year)
        judge       = RuleBasedJudge()
        judge_res   = judge.evaluate(recommended, water_budget, soil, avg_temp, lang, water_data)

        # ── Status Bar ──────────────────────────────────────────────────────
        wl_map = {1: T['water_low'], 2: T['water_mid'], 3: T['water_high']}
        chips  = [
            f"📍 {label_location(governorate, lang)} / {label_region(governorate, region, lang)}",
            f"{season_str} — {month_name} {year}",
            f"🌡️ {avg_temp}°C",
            f"🪨 {label_soil(soil, lang)}",
            f"📐 {float(w_val):g}×{float(h_val):g} {dim_unit}",
            f"💧 {wl_map[water_budget]}",
        ]
        st.markdown(
            f'<div class="status-bar">✅ {T["analysis_success"]} — ' +
            ''.join(f'<span class="status-chip">{c}</span>' for c in chips) +
            '</div>', unsafe_allow_html=True
        )
        et0_caption = (f"ET₀={water_data['et0_mm_day']} {_label(lang, 'مم/يوم', 'mm/day')}"
                       if water_data['et0_mm_day'] is not None else _label(lang, "ET₀ غير متاح", "ET₀ unavailable"))
        source_label = _et0_source_label(weather['source'], lang)
        st.caption(_label(lang,
            f"مصدر ET₀: {source_label}؛ {et0_caption}؛ متوسط Kc تقديري للمجموعات النباتية = {water_data['kc_mean']}؛ خط الأساس المقارن Kc=0.85. افتراضات التخطيط: توزيع متساوٍ للمساحة، كفاءة تطبيق 90%، بلا خصم للأمطار.",
            f"ET₀ source: {source_label}; {et0_caption}; provisional mean group Kc = {water_data['kc_mean']}; comparison baseline Kc=0.85. Assumptions: equal area per recommended plant, 90% application efficiency, no rainfall credit."))
        if water_data["fallback"]:
            st.warning(_label(lang,
                "تعذر جلب ET₀؛ الأرقام التالية تقدير احتياطي قديم مبني على فئة المياه، وليست حساباً مناخياً.",
                "ET₀ could not be fetched; the figures below use the legacy ordinal fallback, not a weather-based calculation."))
        # ── Metrics ─────────────────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)
        col1.metric(T['weekly_consumption'], f"{water_data['ai_w']:,} {T['liters']}")
        col2.metric(T['traditional'],        f"{water_data['trad_w']:,} {T['liters']}")
        col3.metric(T['water_saving'],       f"{water_data['pct']}%",
                    delta=f"{water_data['saved_w']:,} {T['liters']} {_label(lang, 'مقارنة بخط الأساس', 'vs baseline')}")

        # ── Saving Banner ────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="saving-banner">
            <div class="saving-big">💧 {water_data['pct']}% {T['saving_label']}</div>
            <div style="color:#a5d6a7; font-size:.92rem; margin-top:4px;">
                {water_data['saved_w']:,} {T['liters']} / {T['weekly']} →
                {water_data['trad_y'] - water_data['ai_y']:,} {T['liters']} / {T['yearly']}
            </div>
            <div class="co2-badge">
                🌳 {_label(lang, "تقدير CO₂ من بيانات الكتالوج", "Catalog-based CO₂ proxy")}: {judge_res.get('co2_saved', 0):,} {_label(lang, "كجم/سنة", "kg/year")}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Recommended Plants ───────────────────────────────────────────────
        st.markdown(f"### {T['recommended_plants']}")

        # فلتر
        use_types = [T['all_types']] + sorted(recommended['use'].unique().tolist(),
                                              key=lambda u: label_use(u, lang))
        plant_filter = st.selectbox(f"🔍 {T['plant_filter']}", use_types, key="plant_filter_sel",
                                    format_func=lambda u: u if u == T['all_types'] else label_use(u, lang))

        filtered_df = recommended if plant_filter == T['all_types'] \
                      else recommended[recommended['use'] == plant_filter]

        st.markdown(plant_cards_html(filtered_df, T, lang), unsafe_allow_html=True)
        # ── Optional generative design and independent AI review ────────────
        st.markdown("---")
        st.markdown("### 🧠 " + _label(lang, "خطة تصميم ومراجعة اختيارية بالذكاء الاصطناعي", "Optional Generative Design & Review"))
        if not llm_layer.llm_available():
            st.info("لتفعيل المولّد والحكم: اضبط متغير البيئة OPENROUTER_API_KEY ثم أعد تشغيل التطبيق."
                    if lang == 'ar' else
                    "To enable: set the OPENROUTER_API_KEY environment variable and restart.")
        else:
            _ctx = {
                "country": label_country(country, lang),
                "location": label_location(governorate, lang),
                "region": label_region(governorate, region, lang),
                "soil": label_soil(soil, lang),
                "avg_temp_c": avg_temp, "area_sqm": area_sqm,
                "water_budget_filter_class_1low_3high": water_budget,
                "season": season_str,
            }
            _llm_key = f"llm_{country}_{governorate}_{region}_{soil}_{round(avg_temp)}_{area_sqm}_{water_budget}_{lang}"
            if st.button("✨ ولّد التصميم وخلّي الحكم يراجعه" if lang == 'ar'
                         else "✨ Generate design & get judge review", key="btn_llm"):
                with st.spinner(_label(lang, "مساعد التصميم يعمل...", "AI designer is preparing a plan...")):
                    d = llm_layer.generate_design_plan(_ctx, recommended, lang)
                j = None
                if d["ok"]:
                    with st.spinner(_label(lang, "مراجع الذكاء الاصطناعي يراجع الخطة...", "AI reviewer is assessing the plan...")):
                        j = llm_layer.judge_design(_ctx, recommended, d["plan"], lang)
                st.session_state[_llm_key] = {"design": d, "judge": j}

            res = st.session_state.get(_llm_key)
            if res:
                d, j = res["design"], res["judge"]
                if not d["ok"]:
                    st.error(d["error"])
                else:
                    plan = d["plan"]
                    st.markdown("**🗺️ " + _label(lang, "خطة التصميم المقترحة", "Proposed design plan") + "**")
                    for z in plan.get("zones", []):
                        st.markdown(f"- **{z.get('name','')}** — {z.get('area_pct','?')}% — "
                                    f"{', '.join(z.get('plants', []))}  \n  _{z.get('purpose','')}_")
                    irr = plan.get("irrigation", {})
                    if irr:
                        st.markdown(f"💧 **{irr.get('method','')}** — {irr.get('schedule','')}  \n{irr.get('notes','')}")
                    for ph in plan.get("phases", []):
                        st.markdown(f"**{ph.get('phase','')}** ({ph.get('timing','')}): " + " • ".join(ph.get("actions", [])))
                    for rk in plan.get("risks_and_mitigation", []):
                        st.markdown(f"⚠️ {rk.get('risk','')} ← {rk.get('mitigation','')}")
                    v = plan.get("_validation", {})
                    if v.get("dropped_unknown_plants"):
                        st.caption(_label(lang, "تم حذف نباتات خارج القائمة المعتمدة: ",
                                          "Removed plants that are not in the approved list: ")
                                   + ", ".join(map(str, v["dropped_unknown_plants"])))
                    if not v.get("area_sum_ok", True):
                        st.caption(_label(lang, f"تنبيه: مجموع نسب المناطق = {v.get('area_pct_total')}% وليس 100%.",
                                          f"Note: the zone shares add up to {v.get('area_pct_total')}%, not 100%."))

                    if j and j["ok"]:
                        rv = j["review"]
                        st.markdown("**⚖️ " + _label(lang, "مراجعة الذكاء الاصطناعي التوليدي", "Generative-AI review") + "**")
                        c1, c2 = st.columns([1, 3])
                        c1.metric(_label(lang, "الدرجة", "Score"), f"{rv['score']}/100", rv.get("verdict") or None)
                        c2.write(rv.get("rationale", ""))
                        for k, val in (rv.get("criteria") or {}).items():
                            pct = llm_layer.safe_int(val)
                            if pct is not None:
                                pct = max(0, min(100, pct))
                                st.progress(pct / 100, text=f"{k}: {pct}")
                        for title, key in ((_label(lang, "✅ نقاط القوة", "✅ Strengths"), "strengths"),
                                           (_label(lang, "⚠️ المخاطر", "⚠️ Risks"), "risks"),
                                           (_label(lang, "🔧 تحسينات", "🔧 Improvements"), "improvements"),
                                           (_label(lang, "❓ غير مؤكد", "❓ Unknowns"), "unknowns")):
                            items = rv.get(key) or []
                            if items:
                                st.markdown(f"**{title}**")
                                for it in items:
                                    st.markdown(f"- {it}")
                    elif j:
                        st.error(j["error"])

        # ── Layout 3D ───────────────────────────────────────────────────────
        st.markdown(f"### {T['layout_title']}")
        with st.spinner("جارٍ رسم المخطط..." if lang == 'ar' else "Generating layout..."):
            fig = generate_layout(recommended, w_val, h_val, label_location(governorate, lang),
                                  label_region(governorate, region, lang), season_str, lang, unit=unit_opt)
            show_figure(fig, T['layout_title'], T)
            plt.close(fig)

        st.markdown("---")

        # ── Water Chart ──────────────────────────────────────────────────────
        st.markdown(f"### {T['chart_title']}")
        st.caption(_label(lang,
            f"التقديرات الأسبوعية مبنية على يوم التصميم؛ التقديرات السنوية: {_annual_basis_label(water_data['annual_basis'], lang)}.",
            f"Weekly values use the selected design day's ET₀; annual values use {water_data['annual_basis']}."))
        fig2 = render_water_chart(water_data, T)
        show_figure(fig2, T['chart_title'], T)
        plt.close(fig2)

        st.markdown("---")

        # ── Transparent rule-based score ─────────────────────────────────────
        st.markdown(f"### {T['judge_title']}")
        st.caption(_label(lang,
            "درجة حتمية ناتجة عن أوزان ومعايير مبرمجة؛ ليست نموذج تعلم آلي، ولا تمثل دقة تنبؤية مقاسة.",
            "Deterministic score from programmed weights and criteria; not a trained ML model and not a measured predictive accuracy."))
        score_color = (
            "#ffd600" if judge_res['score'] >= 75 else
            "#69f0ae" if judge_res['score'] >= 50 else
            "#ef5350"
        )
        criteria_html = "".join([
            f'<div class="criteria-bar">'
            f'<span class="criteria-name">{k}</span>'
            f'<div class="bar-outer"><div class="bar-inner" style="width:{v}%"></div></div>'
            f'<span class="bar-val">{v}%</span>'
            f'</div>'
            for k, v in judge_res['criteria'].items()
        ])
        st.markdown(f"""
        <div class="judge-card">
            <div class="judge-score" style="color:{score_color}">{judge_res['score']}/100</div>
            <div class="judge-label">{judge_res['label']}</div>
            <br>
            <div style="color:#69f0ae; font-size:.9rem; font-weight:700; margin-bottom:.5rem">
                {T['judge_criteria']}
            </div>
            {criteria_html}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        ml_res = render_ml_judge(lang, governorate, recommended)
        st.markdown("---")

        render_advanced_intelligence_suite(lang, country, governorate, region, soil, avg_temp, area_sqm, water_budget, water_data, recommended)
        render_irrigation_water_suitability(lang, soil, water_data)

        st.markdown("---")

        # ── Summary ──────────────────────────────────────────────────────────
        ml_summary_row = ""
        if ml_res and ml_res.get("score") is not None:
            ml_summary_row = (
                f'<div class="summary-row"><span>{_label(lang, "التوافق المناخي (تعلم آلي + عميق)", "ML + DL climate match")}</span>'
                f'<b style="color:#69f0ae">{ml_res["score"]:.0f}/100 — {ml_res["n_within"]}/{ml_res["n_modeled"]} '
                f'{_label(lang, "داخل النطاق", "within range")}</b></div>')
        st.markdown(f"### {T['summary_title']}")

        plant_rows = "".join([
            f'<div class="summary-row">'
            f'<span>{"⭐"*int(r["beauty"])} {r["name"] if lang=="ar" else r["name_en"]}</span>'
            f'<b>{r["name_en"] if lang=="ar" else r["name"]} — {label_use(r["use"], lang)} — '
            f'{wi.get(r["water"],"💧")} — {r["temp_min"]}–{r["temp_max"]}°C</b>'
            f'</div>'
            for _, r in recommended.iterrows()
        ])

        best_plant = (
            ("الخريف" if lang == "ar" else "Fall") if season_type in ["معتدل", "معتدل دافئ", "Warm", "Mild"]
            else ("الربيع" if lang == "ar" else "Spring") if season_type in ["بارد", "Cold"]
            else ("الصباح الباكر فقط" if lang == "ar" else "Early morning only")
        )
        best_water = (
            ("الصباح الباكر 6–8 ص" if lang == "ar" else "6–8 AM")
            if avg_temp > 25 else
            ("الصباح أو المساء" if lang == "ar" else "Morning or Evening")
        )
        soil_tip = (
            ("أضف مواد عضوية لتحسين الاحتفاظ بالرطوبة" if lang == "ar"
             else "Add organic matter to improve moisture retention")
            if soil in ["رملية", "رملية صحراوية", "رملية ساحلية", "رملية كلسية", "حصوية", "حصوية جبلية",
                        "صخرية", "صخرية جيرية", "صخرية جرانيتية"]
            else (
                "التربة مناسبة — تأكد من الصرف الجيد" if lang == "ar"
                else "Soil is suitable — ensure good drainage"
            )
        )
        suit_label = (
            ("ممتازة — درجة حرارة مثالية" if lang == "ar" else "Excellent — ideal temperature")
            if 15 <= avg_temp <= 30 else (
                ("جيدة — درجة حرارة مرتفعة" if lang == "ar" else "Good — high temperature")
                if avg_temp > 30 else
                ("مقبولة — احمِ النباتات من البرد" if lang == "ar" else "Acceptable — protect from cold")
            )
        )

        st.markdown(f"""
        <div class="summary-box">
            <div class="summary-title">🌍 {T['location_data']}</div>
            <div class="summary-row"><span>{T['gov_label']}</span><b>{label_location(governorate, lang)}</b></div>
            <div class="summary-row"><span>{T['region_label']}</span><b>{label_region(governorate, region, lang)}</b></div>
            <div class="summary-row"><span>{T['design_date']}</span><b>{day} {month_name} {year}</b></div>
            <div class="summary-row"><span>{T['temp_label']}</span>
                <b>{avg_temp}°C — {source_label}</b></div>
            <div class="summary-row"><span>{T['season_label']}</span><b>{season_str}</b></div>
            <div class="summary-row"><span>{T['soil_label']}</span><b>{label_soil(soil, lang)}</b></div>
            <div class="summary-row"><span>{T['area_label']}</span><b>{float(w_val):g}×{float(h_val):g} {dim_unit} = {area_sqm:,.0f} m²</b></div>
            <div class="summary-row"><span>{T['water_budget']}</span><b>{wl_map[water_budget]}</b></div>
            <div class="summary-row"><span>{_label(lang, "التقييم القاعدي", "Rule-based score")}</span>
                <b style="color:#ffd600">{judge_res['score']}/100 — {judge_res['label']}</b></div>
            {ml_summary_row}
        </div>

        <div class="summary-box">
            <div class="summary-title">🌱 {T['recommended_plants']} ({T['plants_count']}: {len(recommended)})</div>
            {plant_rows}
        </div>

        <div class="summary-box">
            <div class="summary-title">💧 {T['water_analysis']}</div>
            <div class="summary-row">
                <span>{T['weekly_consumption']}</span>
                <b>{water_data['ai_w']:,} {T['liters']}</b>
            </div>
            <div class="summary-row">
                <span>{T['traditional']} ({T['weekly']})</span>
                <b>{water_data['trad_w']:,} {T['liters']}</b>
            </div>
            <div class="summary-row">
                <span>{T['water_saving']} ({T['weekly']})</span>
                <b style="color:#00e676">{water_data['saved_w']:,} {T['liters']}</b>
            </div>
            <div class="summary-row">
                <span>{T['water_saving']} ({T['monthly']})</span>
                <b style="color:#00e676">{round(water_data['saved_w'] * WEEKS_PER_MONTH):,} {T['liters']}</b>
            </div>
            <div class="summary-row">
                <span>{T['water_saving']} ({T['yearly']})</span>
                <b style="color:#00e676; font-size:1.05rem">
                    {water_data['trad_y'] - water_data['ai_y']:,} {T['liters']} ({water_data['pct']}%)
                </b>
            </div>
            <div class="summary-row">
                <span>{_label(lang, "احتجاز CO₂ السنوي (تقديري)", "Estimated annual CO₂ uptake")}</span>
                <b style="color:#69f0ae">
                    ~{judge_res.get('co2_saved', 0):,} {_label(lang, "كجم/سنة", "kg/year")}
                </b>
            </div>
        </div>

        <div class="summary-box">
            <div class="summary-title">🔬 {T['scientific_rec']}</div>
            <div class="summary-row"><span>{T['best_planting']}</span><b>{best_plant}</b></div>
            <div class="summary-row"><span>{T['best_watering']}</span><b>{best_water}</b></div>
            <div class="summary-row"><span>{T['soil_improvement']}</span><b>{soil_tip}</b></div>
            <div class="summary-row">
                <span>{T['env_impact']}</span>
                <b>{water_data['trad_y'] - water_data['ai_y']:,} {T['liters']}/yr
                = {round((water_data['trad_y'] - water_data['ai_y']) / 1000)} m³/yr</b>
            </div>
            <div class="summary-row"><span>{T['season_suitability']}</span><b>{suit_label}</b></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Feedback ─────────────────────────────────────────────────────────
        st.markdown(f"### {T['feedback_title']}")
        feedback_opts = T['feedback_options']
        st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
        rating  = st.radio(T['feedback_q'], feedback_opts, horizontal=True, key="rating_radio")
        comment = st.text_area(T['feedback_comment'], placeholder="...", height=80, key="comment_area")
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1:
            if st.button(T['feedback_submit'], key="fb_submit"):
                if save_feedback(governorate, region, rating, comment, judge_res['score'], lang):
                    st.success(T['feedback_thanks'])
                else:
                    st.error(_label(lang, "تعذر حفظ التقييم (لا توجد صلاحية كتابة في مجلد التطبيق).",
                                    "The rating could not be saved (no write permission in the app folder)."))
                fb_data = load_feedback_stats()
                if len(fb_data) > 0:
                    st.info(f"📊 {'إجمالي التقييمات' if lang=='ar' else 'Total ratings'}: {len(fb_data)}")
        with col_fb2:
            if st.button(
                "🔄 تصميم جديد" if lang == 'ar' else "🔄 New Design",
                key="new_design"
            ):
                st.session_state.form_step    = 1
                st.session_state.results_done = False
                st.session_state.form_data    = {}
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # ── System Stats ──────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"### 📊 {T['stats_title']}")
        db_count = len(get_plants_database())
        st.markdown(f"""
        <div class="stats-grid">
            <div class="stats-card">
                <div class="stats-num">{db_count}</div>
                <div class="stats-lbl">{T['total_plants_db']}</div>
            </div>
            <div class="stats-card">
                <div class="stats-num">{len(GOVERNORATE_DATA)}</div>
                <div class="stats-lbl">{T['mapped_locations_count']}</div>
            </div>
            <div class="stats-card">
                <div class="stats-num">{len(ALL_SOIL_TYPES)}</div>
                <div class="stats-lbl">{T['soil_types_count']}</div>
            </div>
            <div class="stats-card">
                <div class="stats-num">{_label(lang, "قاعدي + تعلم آلي", "Rules + ML")}</div>
                <div class="stats-lbl">{T['scoring_method']}</div>
            </div>
            <div class="stats-card">
                <div class="stats-num">{water_data['pct']}%</div>
                <div class="stats-lbl">{T['saving_label']}</div>
            </div>
            <div class="stats-card">
                <div class="stats-num">{judge_res['score']}</div>
                <div class="stats-lbl">{_label(lang, "درجة التقييم القاعدي", "Rule-based score")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Footer ────────────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="text-align:center; padding:2rem 0 1rem; color:#2e4a30; font-size:0.8rem;">
            🌿 حسونة جرين — تخطيط مستدام للأراضي — Hassouna Green
            {creators_html(T)}
        </div>
        """, unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
