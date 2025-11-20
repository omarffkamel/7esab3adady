import streamlit as st
import pandas as pd
import re
from collections import OrderedDict

# --- Utilities ---
ABJAD = {
    'ا':1,'أ':1,'إ':1,'آ':1,'ب':2,'ج':3,'د':4,'ه':5,'و':6,'ز':7,'ح':8,'ط':9,
    'ي':10,'ى':10,'ك':20,'ل':30,'م':40,'ن':50,'س':60,'ع':70,'ف':80,'ص':90,
    'ق':100,'ر':200,'ش':300,'ت':400,'ث':500,'خ':600,'ذ':700,'ض':800,'ظ':900,'غ':1000
}

ELEMENT = {
    'ا':'نار','أ':'نار','إ':'نار','آ':'نار','ه':'نار','ط':'نار','م':'نار','ف':'نار','ش':'نار','ذ':'نار',
    'ب':'تراب','و':'تراب','ي':'تراب','ى':'تراب','ن':'تراب','ص':'تراب','ت':'تراب','ض':'تراب',
    'ج':'هواء','ز':'هواء','ك':'هواء','س':'هواء','ق':'هواء','ث':'هواء','ظ':'هواء',
    'د':'ماء','ح':'ماء','ل':'ماء','ع':'ماء','ر':'ماء','خ':'ماء','غ':'ماء'
}

DIACRITICS = re.compile(r'[\u064B-\u0652\u0640]')

def normalize_ar(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = t.strip()
    t = DIACRITICS.sub('', t)
    t = t.replace('\u200f', '')
    t = t.replace('أ','ا').replace('إ','ا').replace('آ','ا')
    t = t.replace('ى','ي')
    t = re.sub(r'[^\u0600-\u06FF ]+', '', t)
    return t

def analyze_word(word: str):
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

def analyze_multi(text: str):
    text = normalize_ar(text)
    words = [w for w in text.split() if w]
    out = []
    for w in words:
        df, total = analyze_word(w)
        counts = df['العنصر'].value_counts().to_dict() if not df.empty else {}
        out.append({
            'word': w,
            'total': total,
            'unique_len': len(df),
            'نار': counts.get('نار', 0),
            'تراب': counts.get('تراب', 0),
            'هواء': counts.get('هواء', 0),
            'ماء': counts.get('ماء', 0),
        })
    return pd.DataFrame(out)

# --- UI ---
st.set_page_config(page_title="الحساب العددي", layout="centered")
st.title("الحساب العددي")

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

word = st.text_input("Enter word")
if word:
    df, total = analyze_word(word)
    st.markdown(f"**Word (normalized):** `{normalize_ar(word)}`")
    st.markdown(f"**Total Abjad value (unique letters):** **{total}**")
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
        st.download_button("Download CSV", csv, "abjad_analysis.csv", "text/csv")
    else:
        st.write("No valid Arabic words detected.")

st.markdown("---")
