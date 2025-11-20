import streamlit as st
import pandas as pd
import re

# --- Utilities ---
ABJAD = {
    'ا':1,'أ':1,'إ':1,'آ':1,'ب':2,'ج':3,'د':4,'ه':5,'و':6,'ز':7,'ح':8,'ط':9,
    'ي':10,'ى':10,'ك':20,'ل':30,'م':40,'ن':50,'س':60,'ع':70,'ف':80,'ص':90,
    'ق':100,'ر':200,'ش':300,'ت':400,'ث':500,'خ':600,'ذ':700,'ض':800,'ظ':900,'غ':1000
}

# ELEMENT mapping per workbook instructions (نار، تراب، هواء، ماء)
ELEMENT = {
    # نار
    'ا': 'نار', 'ه': 'نار', 'ط': 'نار', 'م': 'نار', 'ف': 'نار', 'ش': 'نار', 'ذ': 'نار',
    # تراب
    'ب': 'تراب', 'و': 'تراب', 'ي': 'تراب', 'ى': 'تراب', 'ن': 'تراب', 'ص': 'تراب', 'ت': 'تراب', 'ض': 'تراب',
    # هواء
    'ج': 'هواء', 'ز': 'هواء', 'ك': 'هواء', 'س': 'هواء', 'ق': 'هواء', 'ث': 'هواء', 'ظ': 'هواء',
    # ماء
    'د': 'ماء', 'ح': 'ماء', 'ل': 'ماء', 'ع': 'ماء', 'ر': 'ماء', 'خ': 'ماء', 'غ': 'ماء'
}

DIACRITICS_TATWEEL = re.compile(r'[\u064B-\u0652\u0640]')

def normalize_ar(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.strip()
    # remove common Arabic diacritics and tatweel
    t = DIACRITICS_TATWEEL.sub('', t)
    # remove RTL mark if present
    t = t.replace('\u200f', '')
    # normalize alef variants -> ا, alef maqsura -> ي
    t = t.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    t = t.replace('ى', 'ي')
    # keep Arabic block letters and spaces only
    t = re.sub(r'[^\u0600-\u06FF ]+', '', t)
    return t

def analyze_word(word: str):
    w = normalize_ar(word)
    letters = list(w)
    rows = []
    total = 0
    for ch in letters:
        if ch == ' ':
            continue
        val = ABJAD.get(ch, 0)
        elt = ELEMENT.get(ch, 'unknown')
        rows.append({'letter': ch, 'value': val, 'element': elt})
        total += val
    df = pd.DataFrame(rows)
    return df, total

def analyze_multi(text: str):
    text = normalize_ar(text)
    words = [w for w in text.split() if w]
    out = []
    for w in words:
        df, tot = analyze_word(w)
        counts = df['element'].value_counts().to_dict() if not df.empty else {}
        rec = {
            'word': w,
            'total': tot,
            'len': len([c for c in w if c != ' ']),
            'نار': counts.get('نار', 0),
            'تراب': counts.get('تراب', 0),
            'هواء': counts.get('هواء', 0),
            'ماء': counts.get('ماء', 0)
        }
        out.append(rec)
    return pd.DataFrame(out)

# --- Streamlit UI ---
st.set_page_config(page_title="Abjad + Element Analyzer", layout="centered")
st.title("الحساب العددي")

word = st.text_input("Enter word")
if word:
    df, total = analyze_word(word)
    st.markdown(f"**Word (normalized):** `{normalize_ar(word)}`  ")
    st.markdown(f"**Total Abjad value:** **{total}**")
    if not df.empty:
        st.dataframe(df)
    else:
        st.write("No Arabic letters detected.")

st.markdown("---")
multi = st.text_area("Enter multiple words")
if multi:
    df_multi = analyze_multi(multi)
    if not df_multi.empty:
        st.dataframe(df_multi)
        csv = df_multi.to_csv(index=False)
        st.download_button("Download CSV", csv, file_name="abjad_analysis.csv", mime="text/csv")
    else:
        st.write("No valid Arabic words detected.")

st.markdown("---")
