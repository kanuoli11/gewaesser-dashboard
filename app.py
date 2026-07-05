import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import urllib.parse
from modules.pegel import load_pegel

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Kanuportal Deutschland 2.0",
    layout="wide",
    page_icon="🛶"
)

# =========================
# STYLING
# =========================
st.markdown("""
<style>
.main { background-color:#eef4f7; }

h1 { color:#0d3b66; }
h2 { color:#145374; }

div[data-testid="stMetric"]{
    background:white;
    border-radius:12px;
    padding:16px;
    box-shadow:0px 2px 8px rgba(0,0,0,0.08);
}

section[data-testid="stSidebar"]{
    background:#d9edf7;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("# 🛶 Kanuportal Deutschland 2.0")
st.caption("Pegel • Sperrungen • Hochwasser • Naturschutz")

st.info("Zentrale Plattform für Kanuinformationen in Deutschland (Version 2.0)")

# =========================
# BUNDESLÄNDER
# =========================
BL_MAP = {
    "Baden-Württemberg": "BW", "Bayern": "BY", "Berlin": "BE", "Brandenburg": "BB",
    "Bremen": "HB", "Hamburg": "HH", "Hessen": "HE", "Mecklenburg-Vorpommern": "MV",
    "Niedersachsen": "NI", "Nordrhein-Westfalen": "NW", "Rheinland-Pfalz": "RP",
    "Saarland": "SL", "Sachsen": "SN", "Sachsen-Anhalt": "ST",
    "Schleswig-Holstein": "SH", "Thüringen": "TH"
}

# =========================
# MANUELLE DATEN (LATER -> JSON)
# =========================
SPERRUNGEN = [
    {
        "Gewässer": "Isar",
        "Abschnitt": "Freising bis Landshut",
        "Bundesland": "Bayern",
        "Typ": "Umweltschutz",
        "Status": "Vogelschutz-Zeitregelung aktiv",
        "Gültig_bis": "2026-07-31",
        "Link": ""
    },
    {
        "Gewässer": "Rur",
        "Abschnitt": "Eifel",
        "Bundesland": "Nordrhein-Westfalen",
        "Typ": "Pegelabhängig",
        "Status": "Befahrbar nur bei grünem Pegel",
        "Gültig_bis": "2027-12-31",
        "Link": ""
    }
]



df_pegel = load_pegel()

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("## 🗺 Navigation")

    bundeslaender = ["Alle"] + list(BL_MAP.keys())
    bl = st.selectbox("Bundesland", bundeslaender)

    typ_filter = st.multiselect(
        "Typ",
        ["Umweltschutz", "Pegelabhängig", "Regulierung"],
        default=["Umweltschutz", "Pegelabhängig", "Regulierung"]
    )

# =========================
# FILTER SPERRUNGEN
# =========================
today = date.today()

aktive = []
archiv = []

for s in SPERRUNGEN:
    if datetime.strptime(s["Gültig_bis"], "%Y-%m-%d").date() >= today:
        aktive.append(s)
    else:
        archiv.append(s)

df_a = pd.DataFrame(aktive)
df_b = pd.DataFrame(archiv)

if bl != "Alle":
    df_a = df_a[df_a["Bundesland"] == bl]
    df_b = df_b[df_b["Bundesland"] == bl]

df_a = df_a[df_a["Typ"].isin(typ_filter)]
df_b = df_b[df_b["Typ"].isin(typ_filter)]

# =========================
# KPI BOXES
# =========================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Pegelstationen", len(df_pegel))

with c2:
    st.metric("Aktive Sperrungen", len(df_a))

with c3:
    st.metric("Archiv", len(df_b))

with c4:
    st.metric("Datum", datetime.now().strftime("%d.%m.%Y"))

# =========================
# MAIN AREA
# =========================
search = st.text_input("🔍 Suche nach Gewässer")

col1, col2 = st.columns(2)

# -------- Sperrungen --------
with col1:
    st.markdown("## ⚠️ Sperrungen")

    view = df_a.copy()
    if search:
        view = view[view["Gewässer"].str.contains(search, case=False)]

    if view.empty:
        st.success("Keine aktiven Meldungen")
    else:
        for _, r in view.iterrows():
            with st.expander(f"{r['Gewässer']} – {r['Abschnitt']}"):
                st.write("Typ:", r["Typ"])
                st.write(r["Status"])

# -------- Pegel --------
with col2:
    st.markdown("## 🌊 Pegelstände")

    pview = df_pegel.copy()
    if search:
        pview = pview[pview["Gewässer"].str.contains(search, case=False, na=False)]

    st.dataframe(pview, use_container_width=True)

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Kanuportal Deutschland 2.0 – Basisversion (refactored)")
