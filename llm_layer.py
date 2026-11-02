"""
llm_layer.py — طبقة الذكاء الاصطناعي (LLM) للمنصة
=====================================================
مودلين مجانيين من شركتين مختلفتين عن قصد:
  - DESIGN_MODEL : Gemma 4 31B (Google)      -> يولّد خطة التصميم
  - JUDGE_MODEL  : Inkling (Thinking Machines) -> يراجع ويقيّم الخطة

لتغيير أي مودل (مثلاً لمودل مدفوع أو مودل بتاعك) غيّر سطر واحد بس
في الإعدادات تحت، أو ضبط متغير بيئة بنفس الاسم. باقي المنصة مش بتتأثر.

المفتاح بيتقرأ من متغير البيئة OPENROUTER_API_KEY (أو st.secrets).
متكتبوش جوه الكود أبداً.

Model replies are free text, so every field is normalised before the app
shows it: numbers such as "85%" become 85, a single string where a list is
expected becomes a one-item list, and unknown plants are dropped. A reply that
is not valid JSON is removed from the cache so "try again" really retries.
"""
import os
import re
import json
import time
import hashlib
import requests

# ───────────────────────── الإعدادات (غيّر من هنا) ─────────────────────────
BASE_URL     = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
# Each role has a list of free models. The first one is tried first; if it is
# rate-limited (429), unavailable (404), slow or returns unusable JSON, the app
# moves on to the next one automatically. You can override a list with
# DESIGN_MODEL / JUDGE_MODEL (one name, or several separated by commas), set
# either as an environment variable or in Streamlit secrets.
_DEFAULT_DESIGN_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "recursive/flint-v1.0:free",
]
_DEFAULT_JUDGE_MODELS = [
    "thinkingmachines/inkling:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-3.5-super-vl:free",
]


def _setting(name):
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name)
    except Exception:
        return None


def _model_chain(name, defaults):
    custom = _setting(name)
    if custom:
        names = [m.strip() for m in str(custom).split(",") if m.strip()]
        if names:
            return names
    return list(defaults)


def design_models():
    return _model_chain("DESIGN_MODEL", _DEFAULT_DESIGN_MODELS)


def judge_models():
    return _model_chain("JUDGE_MODEL", _DEFAULT_JUDGE_MODELS)


# The cache lives next to this file, so it does not depend on the folder the app is started from.
CACHE_FILE   = os.environ.get("LLM_CACHE_FILE",
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_cache.json"))
TIMEOUT_S    = 90
MAX_RETRIES  = 2
# ────────────────────────────────────────────────────────────────────────────


def _msg(lang, ar, en):
    return ar if lang == "ar" else en


def _get_api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    try:  # streamlit secrets (اختياري)
        import streamlit as st
        return st.secrets.get("OPENROUTER_API_KEY")
    except Exception:
        return None


def llm_available():
    return bool(_get_api_key())


# ───────────────────────────── الكاش على الهارد ─────────────────────────────
def _load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache):
    try:
        tmp = CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
        os.replace(tmp, CACHE_FILE)
    except Exception:
        pass


def _cache_key(model, system, user):
    return hashlib.sha256(f"{model}||{system}||{user}".encode("utf-8")).hexdigest()


def forget_cached(model, system, user):
    """Remove one cached reply (used when the reply turned out to be unusable)."""
    cache = _load_cache()
    if cache.pop(_cache_key(model, system, user), None) is not None:
        _save_cache(cache)


# ───────────────────────────── النداء الأساسي ──────────────────────────────
def _call_one(model, system, user, temperature, max_tokens, use_cache, lang, max_retries):
    """Returns (text, error, fatal). fatal=True means another model would fail too (bad key, no credit)."""
    key = _get_api_key()
    if not key:
        return None, _msg(lang, "OPENROUTER_API_KEY غير موجود في متغيرات البيئة.",
                          "OPENROUTER_API_KEY is not set in the environment."), True

    ck = _cache_key(model, system, user)
    if use_cache:
        cache = _load_cache()
        if ck in cache:
            return cache[ck], None, False

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    # Gemma (مقدّم الخدمة بتاعه مبيتدربش): نمنع أي مقدّم بيتدرب
    if model.startswith("google/"):
        payload["provider"] = {"data_collection": "deny"}

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-Title": "Hassouna Green",
    }

    last_err = _msg(lang, "خطأ غير معروف.", "Unknown error.")
    for attempt in range(max_retries + 1):
        try:
            r = requests.post(f"{BASE_URL}/chat/completions", headers=headers,
                              json=payload, timeout=TIMEOUT_S)
            if r.status_code == 200:
                data = r.json()
                text = data["choices"][0]["message"]["content"]
                if use_cache and text:
                    cache = _load_cache()
                    cache[ck] = text
                    _save_cache(cache)
                return text, None, False
            if r.status_code == 429:
                last_err = _msg(lang, "وصلت للحد اليومي/الدقيقي للمودلات المجانية (429). جرّب بعد شوية.",
                                "The free models' rate limit was reached (429). Try again in a little while.")
                time.sleep(2 * (attempt + 1))
                continue
            if r.status_code in (401, 402, 403):
                return None, _msg(lang, f"رفض الطلب ({r.status_code}): {r.text[:200]}",
                                  f"Request refused ({r.status_code}): {r.text[:200]}"), True
            if r.status_code == 404:
                return None, _msg(lang,
                                  "المودل ده مش متاح لحسابك (404). راجع إعدادات الخصوصية في OpenRouter "
                                  "أو غيّر اسم المودل في llm_layer.py.",
                                  "This model is not available to your account (404). Check your OpenRouter "
                                  "privacy settings or change the model name in llm_layer.py."), False
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.Timeout:
            last_err = _msg(lang, "انتهت مهلة الطلب.", "The request timed out.")
        except Exception as e:  # noqa
            last_err = _msg(lang, f"خطأ اتصال: {e}", f"Connection error: {e}")
        time.sleep(1.5 * (attempt + 1))
    return None, last_err, False


def call_llm(model, system, user, temperature=0.3, max_tokens=1800, use_cache=True, lang="ar"):
    """يرجّع (text, error). واحد منهم None دايماً."""
    text, err, _ = _call_one(model, system, user, temperature, max_tokens, use_cache, lang, MAX_RETRIES)
    return text, err


def call_with_fallback(models, system, user, accept, temperature=0.3, max_tokens=1800, lang="ar"):
    """Try each model in turn until one returns a reply that ``accept(text)`` approves.

    Returns (text, error, model_used). Unusable replies are removed from the cache.
    Only the last model gets the full retry-with-wait treatment; earlier ones fail fast
    so the app moves to the next model instead of making the person wait.
    """
    last_err = _msg(lang, "خطأ غير معروف.", "Unknown error.")
    for i, model in enumerate(models):
        retries = MAX_RETRIES if i == len(models) - 1 else 0
        text, err, fatal = _call_one(model, system, user, temperature, max_tokens, True, lang, retries)
        if err:
            last_err = err
            if fatal:
                return None, err, None
            continue
        if accept(text):
            return text, None, model
        forget_cached(model, system, user)
        last_err = _msg(lang, "رد المودل مكانش صالح.", "The model's reply was not usable.")
    return None, last_err, None


def _extract_json(text):
    """يطلّع أول JSON object من رد المودل حتى لو لفّه بـ ```."""
    if not text:
        return None
    text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


# ───────────────────────────── تنظيف رد المودل ─────────────────────────────
def safe_int(value):
    """Return an int from 85, 85.4, "85", "85%" or "85/100"; None if there is no number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(round(value)) if value == value else None  # NaN check
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return int(round(float(match.group()))) if match else None


def _text(value):
    return "" if value is None else str(value).strip()


def _text_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [_text(v) for v in value if _text(v)]
    return [_text(value)] if _text(value) else []


def _dict_list(value):
    if isinstance(value, dict):
        value = [value]
    return [v for v in value if isinstance(v, dict)] if isinstance(value, (list, tuple)) else []


def _plants_brief(recommended):
    rows = []
    for _, r in recommended.iterrows():
        rows.append({
            "name": r.get("name"),
            "name_en": r.get("name_en"),
            "catalog_water_filter_class_1to3": safe_int(r.get("water")) or 0,
            "temp_range_c": [safe_int(r.get("temp_min")) or 0, safe_int(r.get("temp_max")) or 0],
            "use": r.get("use"),
            "beauty_1to5": safe_int(r.get("beauty")) or 0,
            "co2_kg_year": safe_int(r.get("co2")) or 0,
        })
    return rows


def _lang_name(lang):
    return "Modern Standard Arabic" if lang == "ar" else "English"


# ─────────────────────────── 1) مصمم الخطة ───────────────────────────────
def generate_design_plan(ctx, recommended, lang="ar"):
    """
    ctx: dict فيه governorate, region, soil, avg_temp, area_sqm, water_budget, season
    يرجّع dict: {"ok": bool, "plan": {...}, "error": str|None}
    """
    plants = _plants_brief(recommended)
    # The model may answer with either the Arabic or the English plant name.
    to_internal = {}
    for p in plants:
        for n in (p["name"], p["name_en"]):
            if n:
                to_internal[_text(n)] = p["name"]
    display = {p["name"]: (p["name_en"] if lang == "en" and p["name_en"] else p["name"]) for p in plants}

    system = (
        "You are an agricultural landscape designer working across Egypt, the UAE and Qatar. "
        "Use water-saving principles and ONLY the plants provided in the list. "
        "Do not invent plants, numbers or sources. Reply with ONE valid JSON object and "
        f"nothing else. Write all text values in {_lang_name(lang)}."
    )
    user = json.dumps({
        "task": "Design a planting and irrigation plan for this site.",
        "site": ctx,
        "allowed_plants": plants,
        "required_json_schema": {
            "zones": [{"name": "str", "plants": ["must be from allowed_plants[].name"],
                       "area_pct": "int, all zones sum to 100", "purpose": "str"}],
            "irrigation": {"method": "str", "schedule": "str", "notes": "str"},
            "phases": [{"phase": "str", "timing": "str", "actions": ["str"]}],
            "risks_and_mitigation": [{"risk": "str", "mitigation": "str"}],
        },
        "rules": ["2 to 4 zones", "2 to 3 phases",
                  "area_pct must sum to 100",
                  "be practical for the stated soil and temperature"],
    }, ensure_ascii=False)

    def _good(t):
        j = _extract_json(t)
        return bool(j and _dict_list(j.get("zones")))

    text, err, used = call_with_fallback(design_models(), system, user, _good,
                                         temperature=0.5, max_tokens=2200, lang=lang)
    if err:
        return {"ok": False, "plan": None, "error": err}
    raw = _extract_json(text)

    # ── تحقق بعدي (Guardrails): نشيل أي نبات المودل اخترعه ونوحّد شكل البيانات ──
    dropped, zones = [], []
    for z in _dict_list(raw.get("zones")):
        kept = []
        for p in _text_list(z.get("plants")):
            if p in to_internal:
                kept.append(display[to_internal[p]])
            else:
                dropped.append(p)
        zones.append({"name": _text(z.get("name")), "plants": kept,
                      "area_pct": safe_int(z.get("area_pct")) or 0, "purpose": _text(z.get("purpose"))})
    irrigation = raw.get("irrigation") if isinstance(raw.get("irrigation"), dict) else {}
    plan = {
        "zones": zones,
        "irrigation": {k: _text(irrigation.get(k)) for k in ("method", "schedule", "notes") if _text(irrigation.get(k))},
        "phases": [{"phase": _text(ph.get("phase")), "timing": _text(ph.get("timing")),
                    "actions": _text_list(ph.get("actions"))} for ph in _dict_list(raw.get("phases"))],
        "risks_and_mitigation": [{"risk": _text(rk.get("risk")), "mitigation": _text(rk.get("mitigation"))}
                                 for rk in _dict_list(raw.get("risks_and_mitigation"))],
    }
    total = sum(z["area_pct"] for z in zones)
    plan["_model"] = used
    plan["_validation"] = {
        "dropped_unknown_plants": dropped,
        "area_pct_total": total,
        "area_sum_ok": total == 100,
    }
    return {"ok": True, "plan": plan, "error": None}


# ──────────────────────────── 2) مراجع الخطة ─────────────────────────────
def judge_design(ctx, recommended, plan, lang="ar"):
    """
    الحكم بيراجع الخطة اللي ولّدها مودل تاني (شركة تانية = تقييم أنزه).
    يرجّع dict: {"ok": bool, "review": {...}, "error": str|None}
    """
    system = (
        "You are a strict, evidence-minded reviewer of land-reclamation designs for a "
        "science competition. Judge ONLY from the data given; if something is unknown, "
        "say it is unknown instead of guessing. Penalise unrealistic claims. Reply with "
        f"ONE valid JSON object and nothing else. Write text values in {_lang_name(lang)}."
    )
    user = json.dumps({
        "task": "Review the proposed design for this site.",
        "site": ctx,
        "recommended_plants": _plants_brief(recommended),
        "proposed_plan": plan,
        "required_json_schema": {
            "score": "int 0-100",
            "verdict": "one of: excellent | good | needs_work",
            "criteria": {"water_efficiency": "0-100", "climate_fit": "0-100",
                         "soil_fit": "0-100", "practicality": "0-100",
                         "internal_consistency": "0-100"},
            "strengths": ["str"],
            "risks": ["str"],
            "improvements": ["str"],
            "rationale": "2-3 sentences",
            "unknowns": ["what you could not verify from the data"],
        },
    }, ensure_ascii=False)

    def _good(t):
        j = _extract_json(t)
        return bool(j and safe_int(j.get("score")) is not None)

    text, err, used = call_with_fallback(judge_models(), system, user, _good,
                                         temperature=0.1, max_tokens=1800, lang=lang)
    if err:
        return {"ok": False, "review": None, "error": err}
    raw = _extract_json(text)
    score = safe_int(raw.get("score"))
    criteria = {}
    if isinstance(raw.get("criteria"), dict):
        for k, v in raw["criteria"].items():
            n = safe_int(v)
            if n is not None:
                criteria[_text(k)] = max(0, min(100, n))
    review = {
        "score": max(0, min(100, score)),
        "verdict": _text(raw.get("verdict")),
        "criteria": criteria,
        "strengths": _text_list(raw.get("strengths")),
        "risks": _text_list(raw.get("risks")),
        "improvements": _text_list(raw.get("improvements")),
        "rationale": _text(raw.get("rationale")),
        "unknowns": _text_list(raw.get("unknowns")),
        "model": used,
    }
    return {"ok": True, "review": review, "error": None}
