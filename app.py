import streamlit as st
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
import requests
import pandas as pd
from datetime import datetime, date
import urllib.parse

# SPRECHENDE TITEL UND LAYOUT EINRICHTEN
st.set_page_config(page_title="Kanu- & Paddel-Dashboard Deutschland", layout="wide", page_icon="🛶")

st.title("🛶 Bundesweites Kanu- & Paddel-Dashboard")
st.subheader("Echtzeit-Pegel, Befahrungsregelungen, Sperrungen und Umweltwarnungen")

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
# Du kannst jetzt bei jedem Eintrag ganz einfach ein Feld "Link": "https://..." hinzufügen.
# Wenn du keinen Link hast, schreibe einfach "Link": "" oder lass es weg.

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
hw_data = get_hochwasser_status()

# ==========================================
# DASHBOARD SIDEBAR (FILTER)
# ==========================================
st.sidebar.header("🗺️ Filter-Optionen")
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
# DATEN VERARBEITEN (AKTUELL VS. ARCHIV)
# ==========================================
heute = date.today()
aktive_meldungen = []
archiv_meldungen = []

for meldung in SPERRUNGEN_DATENBANK:
    ablauf_datum = datetime.strptime(meldung["Gültig_bis"], "%Y-%m-%d").date()
    if ablauf_datum >= heute:
        aktive_meldungen.append(meldung)
    else:
        archiv_meldungen.append(meldung)

df_aktiv = pd.DataFrame(aktive_meldungen) if aktive_meldungen else pd.DataFrame(columns=["Gewässer", "Abschnitt", "Bundesland", "Typ", "Status", "Gültig_bis", "Link"])
df_archiv = pd.DataFrame(archiv_meldungen) if archiv_meldungen else pd.DataFrame(columns=["Gewässer", "Abschnitt", "Bundesland", "Typ", "Status", "Gültig_bis", "Link"])

if selected_bl != "Alle Bundesländer":
    df_aktiv = df_aktiv[df_aktiv["Bundesland"] == selected_bl]
    df_archiv = df_archiv[df_archiv["Bundesland"] == selected_bl]
    
df_aktiv = df_aktiv[df_aktiv["Typ"].isin(info_typ)]
df_archiv = df_archiv[df_archiv["Typ"].isin(info_typ)]

# ==========================================
# HAUPTBEREICH: ANZEIGE
# ==========================================
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### ⚠️ Aktuelle Sperrungen & Kanu-Hinweise")
    
    if df_aktiv.empty:
        st.success("✅ Keine aktiven Sperrungen oder Warnungen für die aktuelle Auswahl gemeldet!")
    else:
        for index, row in df_aktiv.iterrows():
            with st.expander(f"{row['Status'].split()[0] if row['Status'].split() else ''} {row['Gewässer']} ({row['Abschnitt']}) - {row['Bundesland']}"):
                st.write(f"**Grund/Typ:** {row['Typ']}")
                st.write(f"**Details:** {row['Status']}")
                
                # Prüfen, ob ein Link existiert und Button anzeigen
                if "Link" in row and row["Link"]:
                    st.link_button("🌐 Mehr Infos auf externer Webseite", row["Link"])
                
                ziel_datum = datetime.strptime(row["Gültig_bis"], "%Y-%m-%d").strftime("%d.%m.%Y")
                st.caption(f"Diese Meldung wird automatisch angezeigt bis: {ziel_datum}")

    st.markdown("---")
    st.markdown("### 📂 Archiv: Kürzlich abgelaufene Infos")
    if df_archiv.empty:
        st.caption("Keine abgelaufenen Meldungen im Archiv für diese Auswahl.")
    else:
        for index, row in df_archiv.iterrows():
            with st.expander(f"⚪ [ABGELAUFEN] {row['Gewässer']} ({row['Abschnitt']})"):
                st.write(f"**Ehemaliger Status:** {row['Status']}")
                
                if "Link" in row and row["Link"]:
                    st.link_button("🌐 Zum alten Info-Link", row["Link"])
                    
                alt_datum = datetime.strptime(row["Gültig_bis"], "%Y-%m-%d").strftime("%d.%m.%Y")
                st.caption(f"Gültigkeit lief ab am: {alt_datum}")

with col2:
    st.markdown("### 🌊 Bundesweite Live-Pegelstände")
    search_river = st.text_input("🔍 Pegel nach Flussnamen filtern (z.B. Donau, Rhein, Isar):", "")
    
    df_pegel_filtered = df_pegel.copy()
    if search_river:
        df_pegel_filtered = df_pegel_filtered[df_pegel_filtered["Gewässer"].str.contains(search_river, case=False, na=False)]
    
    if df_pegel_filtered.empty:
        st.info("Keine Pegelstationen für diesen Suchbegriff gefunden.")
    else:
        st.dataframe(df_pegel_filtered.sort_values(by="Gewässer"), use_container_width=True, hide_index=True)

# ==========================================
# INTELLIGENTER DKV-EXTERN-LINK
# ==========================================
st.markdown("---")
st.markdown("### 📑 DKV-Befahrungsregelungen (Ergänzende Suche)")
if selected_bl != "Alle Bundesländer":
    encoded_bl = urllib.parse.quote(selected_bl)
    dkv_link = f"https://waters.kanu-efb.de/waters/ShowRestrictions.php?land={encoded_bl}"
    st.info(f"🔗 **Direkt-Link für {selected_bl}:** [Hier klicken für alle DKV-Regelungen in {selected_bl}]({dkv_link})")
else:
    st.info("🔗 **Gesamt-Datenbank:** [Hier geht es direkt zur vollständigen DKV-Befahrungsdatenbank (kanu-efb.de)](https://waters.kanu-efb.de/waters/ShowRestrictions.php)")

# ==========================================
# QUELLEN-BOX GANZ UNTEN
# ==========================================
st.markdown("---")
st.markdown("#### ℹ️ Genutzte Quellen")
st.caption("""
* **PEGELONLINE API:** Wasserstraßen- und Schifffahrtsverwaltung des Bundes (WSV) – Automatische Echtzeit-Pegelstände der Bundeswasserstraßen.
* **LHP API (Hochwasserzentralen.de):** Länderübergreifendes Hochwasserportal – Automatische, offizielle Hochwasser-Warnmeldungen und Lageberichte der einzelnen Bundesländer.
* **Deutscher Kanu-Verband e.V. (DKV):** Direktverlinkung zur DKV-Gewässerdatenbank für amtliche und vereinsinterne Befahrungsregelungen.
* **Community- & Vereinsdatenbank:** Manuell gepflegte Befahrungsregelungen, temporäre Naturschutz-Sperrungen (z.B. Vogelschutz) und lokale Umweltamt-Warnungen (z.B. Blaualgen).
""")
