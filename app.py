import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import urllib.parse

st.markdown("""
<style>

.main{
    background-color:#eef4f7;
}

h1{
    color:#0d3b66;
}

h2{
    color:#145374;
}

div[data-testid="stMetric"]{

    background:white;

    border-radius:12px;

    padding:18px;

    box-shadow:0px 2px 10px rgba(0,0,0,0.12);

}

div.stButton>button{

    border-radius:10px;

    background:#0d6efd;

    color:white;

}

section[data-testid="stSidebar"]{

    background:#d9edf7;

}

</style>
""",unsafe_allow_html=True)

# SPRECHENDE TITEL UND LAYOUT EINRICHTEN
st.set_page_config(page_title="Kanu- & Paddel-Dashboard Deutschland", layout="wide", page_icon="🛶")

st.markdown("""

# 🛶 Deutsches Kanuportal

### Pegel • Befahrbarkeit • Wetter • Sperrungen • Naturschutz

""")
st.info(
"Willkommen im bundesweiten Kanuportal. "
"Hier findest du Live-Pegelstände, Befahrungsregelungen, Sperrungen und Umweltinformationen."
)


# Mapping für Bundesland-Kürzel
BL_MAP = {
    "Baden-Württemberg": "BW", "Bayern": "BY", "Berlin": "BE", "Brandenburg": "BB", "Bremen": "HB",
    "Hamburg": "HH", "Hessen": "HE", "Mecklenburg-Vorpommern": "MV", "Niedersachsen": "NI",
    "Nordrhein-Westfalen": "NW", "Rheinland-Pfalz": "RP", "Saarland": "SL", "Sachsen": "SN",
    "Sachsen-Anhalt": "ST", "Schleswig-Holstein": "SH", "Thüringen": "TH"
}

# ==========================================
# KONFIGURATION: MANUELLE KANU-DATENBANK (Jetzt mit optionalem Link!)
# ==========================================
SPERRUNGEN_DATENBANK = [
    {
        "Gewässer": "Isar", 
        "Abschnitt": "Freising bis Landshut", 
        "Bundesland": "Bayern", 
        "Typ": "Umweltschutz", 
        "Status": "⚠️ Befahrungsverbot zum Vogelschutz (jährlich von März bis Ende Juli).", 
        "Gültig_bis": "2026-07-31",
        "Link": "https://www.kanu-bayern.de"  # Beispiel-Link
    },
    {
        "Gewässer": "Wiesent", 
        "Abschnitt": "Oberlauf", 
        "Bundesland": "Bayern", 
        "Typ": "Regulierung", 
        "Status": "Obergrenze: Nur über Mindestpegel frei, organisierter Verleih eingeschränkt.", 
        "Gültig_bis": "2026-10-31",
        "Link": ""  # Kein Link vorhanden
    },
    {
        "Gewässer": "Spreewald", 
        "Abschnitt": "Kernzone Fließe", 
        "Bundesland": "Brandenburg", 
        "Typ": "Sperrung", 
        "Status": "🛑 Temporäre Sperrung wegen Niedrigwasser / Krautung.", 
        "Gültig_bis": "2026-06-15",
        "Link": "https://www.lfu.brandenburg.de"
    },
    {
        "Gewässer": "Rur", 
        "Abschnitt": "Eifel-Abschnitte", 
        "Bundesland": "Nordrhein-Westfalen", 
        "Typ": "Pegelabhängig", 
        "Status": "⚠️ Befahrbar nur bei grünem Pegel (Info über Monschau).", 
        "Gültig_bis": "2027-12-31",
        "Link": ""
    },
    {
        "Gewässer": "Aller", 
        "Abschnitt": "Mündungsebene", 
        "Bundesland": "Niedersachsen", 
        "Typ": "Umweltwarnung", 
        "Status": "🦠 Blaualgenwarnung! Hautkontakt und Tränken von Hunden vermeiden.", 
        "Gültig_bis": "2026-09-15",
        "Link": ""
    },
    {
        "Gewässer": "Donau", 
        "Abschnitt": "Obere Donau (Naturpark)", 
        "Bundesland": "Baden-Württemberg", 
        "Typ": "Regulierung", 
        "Status": "🛑 Kontingentierung / Befahrungsverbot bei Pegel unter 46cm (Beuron).", 
        "Gültig_bis": "2028-01-01",
        "Link": "https://www.naturpark-obere-donau.de"
    },
]

# ==========================================
# DATA FETCHING AUTOMATISCH
# ==========================================
@st.cache_data(ttl=600)
def load_live_pegel():
    try:
        url = "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json?includeCurrentMeasurement=true"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            stations_list = []
            for station in response.json():
                if 'currentMeasurement' in station:
                    stations_list.append({
                        "Gewässer": station.get("water", {}).get("shortname", "Unbekannt"),
                        "Station": station.get("name"),
                        "Pegel (cm)": station["currentMeasurement"].get("value"),
                        "Zeitpunkt": station["currentMeasurement"].get("timestamp")
                    })
            return pd.DataFrame(stations_list)
    except:
        pass
    return pd.DataFrame(columns=["Gewässer", "Station", "Pegel (cm)", "Zeitpunkt"])

@st.cache_data(ttl=900)
def get_hochwasser_status():
    try:
        url = "https://www.hochwasserzentralen.de/webservices/get_infosbundesland.php"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        return {}

df_pegel = load_live_pegel()
anzahl_pegel = len(df_pegel)

# Vorab-Verarbeitung für die Kennzahlen-Metriken (Fehlerbehebung)
heute_date = date.today()
aktive_meldungen_init = []
archiv_meldungen_init = []

for meldung in SPERRUNGEN_DATENBANK:
    ablauf_datum = datetime.strptime(meldung["Gültig_bis"], "%Y-%m-%d").date()
    if ablauf_datum >= heute_date:
        aktive_meldungen_init.append(meldung)
    else:
        archiv_meldungen_init.append(meldung)

anzahl_sperrungen = len(aktive_meldungen_init)
anzahl_warnungen = len(archiv_meldungen_init)

heute_str = datetime.now().strftime("%d.%m.%Y")
hw_data = get_hochwasser_status()
c1,c2,c3,c4=st.columns(4)

with c1:
    st.metric("🌊 Pegelstationen",anzahl_pegel)

with c2:
    st.metric("⚠️ Sperrungen",anzahl_sperrungen)

with c3:
    st.metric("📂 Archiv",anzahl_warnungen)

with c4:
    st.metric("📅 Heute",hehte_str if 'hehte_str' in locals() else heute_str)

# ==========================================
# DASHBOARD SIDEBAR (FILTER)
# ==========================================
st.sidebar.image(
"https://upload.wikimedia.org/wikipedia/commons/3/36/Canoe_icon.png",
width=90
)

st.sidebar.title("Navigation")

st.sidebar.markdown("---")
bundeslaender = ["Alle Bundesländer"] + list(BL_MAP.keys())
selected_bl = st.sidebar.selectbox("Wähle ein Bundesland:", bundeslaender)

info_typ = st.sidebar.multiselect(
    "Informationstyp:", 
    ["Sperrung", "Regulierung", "Umweltschutz", "Pegelabhängig", "Umweltwarnung"],
    default=["Sperrung", "Regulierung", "Umweltschutz", "Pegelabhängig", "Umweltwarnung"]
)

# ==========================================
# HOCHWASSER-STATUS LIVE ANZEIGEN
# ==========================================
if selected_bl != "Alle Bundesländer" and hw_data:
    bl_kurz = BL_MAP.get(selected_bl)
    bl_info = hw_data.get(bl_kurz, {})
    if bl_info:
        st.markdown(f"### 📢 Automatischer Hochwasser-Warnstatus ({selected_bl})")
        hw_text = bl_info.get("text", "Keine spezifischen Berichte vorhanden.")
        hw_stufen = bl_info.get("pegel_stufe", "Normalbetrieb")
        
        if "hochwasser" in hw_text.lower() or "warnung" in hw_text.lower():
            st.error(f"⚠️ **Meldung:** {hw_text} (Status: {hw_stufen})")
        else:
            st.success(f"✅ **Meldung:** {hw_text} (Status: {hw_stufen})")
    st.markdown("---")

# ==========================================
# DATEN FILTERN FÜR DIE ANZEIGE
# ==========================================
df_aktiv = pd.DataFrame(aktive_meldungen_init) if aktive_meldungen_init else pd.DataFrame(columns=["Gewässer", "Abschnitt", "Bundesland", "Typ", "Status", "Gültig_bis", "Link"])
df_archiv = pd.DataFrame(archiv_meldungen_init) if archiv_meldungen_init else pd.DataFrame(columns=["Gewässer", "Abschnitt", "Bundesland", "Typ", "Status", "Gültig_bis", "Link"])

if selected_bl != "Alle Bundesländer":
    df_aktiv = df_aktiv[df_aktiv["Bundesland"] == selected_bl]
    df_archiv = df_archiv[df_archiv["Bundesland"] == selected_bl]
    
df_aktiv = df_aktiv[df_aktiv["Typ"].isin(info_typ)]
df_archiv = df_archiv[df_archiv["Typ"].isin(info_typ)]

# ==========================================
# HAUPTBEREICH: ANZEIGE
# ==========================================
suche = st.text_input(
    "🔍 Gewässer suchen",
    placeholder="z.B. Isar"
)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### ⚠️ Aktuelle Sperrungen & Kanu-Hinweise")
    
    # Textsuche auf aktive Sperrungen anwenden
    df_aktiv_display = df_aktiv.copy()
    if suche:
        df_aktiv_display = df_aktiv_display[df_aktiv_display["Gewässer"].str.contains(suche, case=False, na=False)]
        
    if df_aktiv_display.empty:
        st.success("✅ Keine aktiven Sperrungen oder Warnungen für die aktuelle Auswahl gemeldet!")
    else:
        for index, row in df_aktiv_display.iterrows():
            with st.expander(f"{row['Status'].split()[0] if row['Status'].split() else ''} {row['Gewässer']} ({row['Abschnitt']}) - {row['Bundesland']}"):
                st.write(f"**Grund/Typ:** {row['Typ']}")
                st.write(f"**Details:** {row['Status']}")
                
                if "Link" in row and row["Link"]:
                    st.link_button("🌐 Mehr Infos auf externer Webseite", row["Link"])
                
                ziel_datum = datetime.strptime(row["Gültig_bis"], "%Y-%m-%d").strftime("%d.%m.%Y")
                st.caption(f"Diese Meldung wird automatisch angezeigt bis: {ziel_datum}")

    st.markdown("---")
    st.markdown("### 📂 Archiv: Kürzlich abgelaufene Infos")
    
    # Textsuche auf Archiv anwenden
    df_archiv_display = df_archiv.copy()
    if suche:
        df_archiv_display = df_archiv_display[df_archiv_display["Gewässer"].str.contains(suche, case=False, na=False)]
        
    if df_archiv_display.empty:
        st.caption("Keine abgelaufenen Meldungen im Archiv für diese Auswahl.")
    else:
        for index, row in df_archiv_display.iterrows():
            with st.expander(f"⚪ [ABGELAUFEN] {row['Gewässer']} ({row['Abschnitt']})"):
                st.write(f"**Ehemaliger Status:** {row['Status']}")
                
                if "Link" in row and row["Link"]:
                    st.link_button("🌐 Zum alten Info-Link", row["Link"])
                    
                alt_datum = datetime.strptime(row["Gültig_bis"], "%Y-%m-%d").strftime("%d.%m.%Y")
                st.caption(f"Gültigkeit lief ab am: {alt_datum}")

with col2:
    st.markdown("### 🌊 Bundesweite Live-Pegelstände")
    search_river = st.text_input("🔍 Pegel nach Flussnamen filtern (z.B. Donau, Rhein, Isar):", "")
    
    df_pegel_filtered = df_pegel.
