import streamlit as st
import pandas as pd
import re
from collections import OrderedDict
from pathlib import Path

# --- Base paths (script directory) ---
BASE = Path(__file__).resolve().parent

ABJAD_CSV = BASE / "abjad.csv"
ELEMENTS_CSV = BASE / "elements.csv"
A3DAD_CSV = BASE / "a3dad_2.csv"

# --- Helpers to load CSVs if present ---
def load_abjad_from_csv(path: Path):
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        return None
    letter_col = None
    value_col = None
    for c in df.columns:
        lc = c.lower()
        if lc in ("letter", "char", "الحرف"):
            letter_col = c
        if lc in ("value", "val", "القيمة", "value_abjad"):
            value_col = c
    if letter_col is None:
        letter_col = df.columns[0]
    if value_col is None and len(df.columns) > 1:
        value_col = df.columns[1]
    if value_col is None:
        return None
    mapping = {}
    for _, r in df.iterrows():
        ch = str(r[letter_col]).strip()
        try:
            v = int(r[value_col])
        except Exception:
            try:
                v = int(float(r[value_col]))
            except Exception:
                v = 0
        if ch:
            mapping[ch] = v
    return mapping


def load_elements_from_csv(path: Path):
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        return None
    letter_col = df.columns[0]
    elt_col = None
    for c in df.columns:
        if c.lower() in ("element", "العنصر", "element_name"):
            elt_col = c
            break
    if elt_col is None:
        if len(df.columns) > 1:
            elt_col = df.columns[1]
        else:
            return None
    mapping = {}
    for _, r in df.iterrows():
        ch = str(r[letter_col]).strip()
        elt = str(r[elt_col]).strip()
        if ch:
            mapping[ch] = elt
    return mapping

# --- Normalization helpers / regex ---
DIACRITICS = re.compile(r'[\u064B-\u0652\u0640]')

def normalize_ar(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = t.strip()
    t = DIACRITICS.sub('', t)
    t = t.replace('\u200f', '')
    t = t.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    t = t.replace('ى', 'ي')
    t = re.sub(r'[^\u0600-\u06FF ]+', '', t)
    return t

def normalize_letter(ch: str) -> str:
    if not isinstance(ch, str):
        return ""
    ch = ch.strip()
    ch = DIACRITICS.sub('', ch)
    ch = ch.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    ch = ch.replace('ى', 'ي')
    return ch

def load_a3dad_from_csv(path: Path):
    if not path.exists():
        return None, None
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        return None, None

    letter_col = df.columns[0]
    for c in df.columns:
        lc = c.lower()
        if "حرف" in c or lc in ("letter", "char"):
            letter_col = c
            break

    ruh_col = None
    aql_col = None
    nafs_col = None
    for c in df.columns:
        if "روح" in c:
            ruh_col = c
        elif "عقل" in c:
            aql_col = c
        elif "نفس" in c:
            nafs_col = c

    def safe_int(x):
        try:
            return int(x)
        except Exception:
            try:
                return int(float(x))
            except Exception:
                return 0

    mapping = {}
    for _, r in df.iterrows():
        raw_ch = str(r[letter_col]).strip()
        if not raw_ch:
            continue
        ch = normalize_letter(raw_ch)

        ruh = safe_int(r[ruh_col]) if ruh_col else 0
        aql = safe_int(r[aql_col]) if aql_col else 0
        nafs = safe_int(r[nafs_col]) if nafs_col else 0
        mapping[ch] = {"روح": ruh, "عقل": aql, "نفس": nafs}

    return mapping, df

# --- Fallbacks ---
FALLBACK_ABJAD = {
    'ا':1,'أ':1,'إ':1,'آ':1,'ب':2,'ج':3,'د':4,'ه':5,'و':6,'ز':7,'ح':8,'ط':9,
    'ي':10,'ى':10,'ك':20,'ل':30,'م':40,'ن':50,'س':60,'ع':70,'ف':80,'ص':90,
    'ق':100,'ر':200,'ش':300,'ت':400,'ث':500,'خ':600,'ذ':700,'ض':800,'ظ':900,'غ':1000
}
FALLBACK_ELEMENTS = {
    'ا':'نار','أ':'نار','إ':'نار','آ':'نار','ه':'نار','ط':'نار','م':'نار','ف':'نار','ش':'نار','ذ':'نار',
    'ب':'تراب','و':'تراب','ي':'تراب','ى':'تراب','ن':'تراب','ص':'تراب','ت':'تراب','ض':'تراب',
    'ج':'هواء','ز':'هواء','ك':'هواء','س':'هواء','ق':'هواء','ث':'هواء','ظ':'هواء',
    'د':'ماء','ح':'ماء','ل':'ماء','ع':'ماء','ر':'ماء','خ':'ماء','غ':'ماء'
}

ABJAD = load_abjad_from_csv(ABJAD_CSV) or FALLBACK_ABJAD
ELEMENT = load_elements_from_csv(ELEMENTS_CSV) or FALLBACK_ELEMENTS
A3DAD, A3DAD_RAW_DF = load_a3dad_from_csv(A3DAD_CSV)

# --- First-page analysis ---
def analyze_word_abjad_unique(word: str):
    w = normalize_ar(word)
    rows = []
    total = 0
    seen = OrderedDict()
    for ch in w:
        if ch == ' ':
            continue
        if ch in seen:
            continue
        seen[ch] = True
        val = ABJAD.get(ch, 0)
        elt = ELEMENT.get(ch, 'unknown')
        rows.append({'الحرف': ch, 'القيمة': val, 'العنصر': elt})
        total += val
    df = pd.DataFrame(rows)
    return df, total

# --- Second-page analysis ---
def analyze_word_a3dad(word: str):
    w = normalize_ar(word)
    rows = []
    totals = {"روح": 0, "عقل": 0, "نفس": 0}

    if not A3DAD:
        return pd.DataFrame(), w

    seen = OrderedDict()
    for ch in w:
        if ch == ' ':
            continue
        if ch in seen:
            continue
        seen[ch] = True

        vals = A3DAD.get(ch, {"روح": 0, "عقل": 0, "نفس": 0})
        ruh = vals["روح"]
        aql = vals["عقل"]
        nafs = vals["نفس"]

        rows.append({
            "الحرف": ch,
            "روح": ruh,
            "عقل": aql,
            "نفس": nafs,
            "مجموع الحرف": ruh + aql + nafs,
        })

        totals["روح"] += ruh
        totals["عقل"] += aql
        totals["نفس"] += nafs

    if rows:
        rows.append({
            "الحرف": "مجموع النص (بدون تكرار الحروف)",
            "روح": totals["روح"],
            "عقل": totals["عقل"],
            "نفس": totals["نفس"],
            "مجموع الحرف": totals["روح"] + totals["عقل"] + totals["نفس"],
        })

    df = pd.DataFrame(rows)
    return df, w

# --- UI ---
st.set_page_config(page_title="الحساب العددي", layout="centered")

# --- Reverse layout: main left, index right ---
col_main, col_index = st.columns([3, 1])

with col_index:
    page = st.radio("فهرس", ["1", "2"])

with col_main:

    # --- الصفحة الأولى: أبجد ---
    if page == "1":

        st.subheader("قائمة الحروف")

        letters = sorted(set(ABJAD.keys()).union(ELEMENT.keys()))
        rows = []
        for ch in letters:
            rows.append({
                'القيمة': ABJAD.get(ch, 0),
                'العنصر': ELEMENT.get(ch, 'unknown'),
                'الحرف': ch
            })
        df_mapping = pd.DataFrame(rows)[['القيمة', 'العنصر', 'الحرف']]
        st.dataframe(df_mapping, hide_index=True)

        st.markdown("---")

        word = st.text_input(" كلمة")
        if word:
            df, total = analyze_word_abjad_unique(word)
            st.markdown(f"**مجموع القيم:** **{total}**")
            if not df.empty:
                st.dataframe(df, hide_index=True)
            else:
                st.write("لم يتم العثور على حروف عربية.")

        st.markdown("---")

        multi_word_text = st.text_area(" عدة كلمات")
        if multi_word_text:
            df_multi, total_multi = analyze_word_abjad_unique(multi_word_text)
            st.write(f"**مجموع القيم للنص (الحروف غير المكررة):** **{total_multi}**")
            if not df_multi.empty:
                st.dataframe(df_multi, hide_index=True)
            else:
                st.write("لم يتم العثور على حروف عربية في النص.")

    # --- الصفحة الثانية: روح / عقل / نفس ---
    else:

        st.subheader("قائمة الحروف")

        if A3DAD_RAW_DF is not None:
            st.dataframe(A3DAD_RAW_DF, hide_index=True)
        else:
            st.warning("لم يتم العثور على الملف a3dad_2.csv.")

        st.markdown("---")

        word2 = st.text_input(" كلمة")
        if word2:
            df2, norm2 = analyze_word_a3dad(word2)
            if not df2.empty:
                st.dataframe(df2, hide_index=True)
            else:
                st.write("لم يتم العثور على حروف.")

        st.markdown("---")

        multi_text = st.text_area(" عدة كلمات")
        if multi_text:
            df_multi2, norm_multi2 = analyze_word_a3dad(multi_text)
            st.markdown(f"**النص بعد التنقيح:** `{norm_multi2}`")
            if not df_multi2.empty:
                st.dataframe(df_multi2, hide_index=True)
            else:
                st.write("لم يتم العثور على حروف.")
