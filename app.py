import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# SPRECHENDE TITEL UND LAYOUT EINRICHTEN
st.set_page_config(page_title="Kanu- & Paddel-Dashboard Deutschland", layout="wide", page_icon="🛶")

st.title("🛶 Bundesweites Kanu- & Paddel-Dashboard")
st.subheader("Echtzeit-Pegel, Befahrungsregelungen, Sperrungen und Umweltwarnungen für ganz Deutschland")

# ==========================================
# KONFIGURATION: HIER KANNST DU JEDERZEIT ERWEITERN!
# ==========================================
# Wenn ein neues Bundesland, eine neue Sperrung oder ein Umweltalarm dazukommt, 
# kannst du es einfach hier in diesen Listen eintragen.

SPERRUNGEN_DATENBANK = [
    {"Gewässer": "Isar", "Abschnitt": "Freising bis Landshut", "Bundesland": "Bayern", "Typ": "Umweltschutz", "Status": "⚠️ Befahrungsverbot (01.03. - 31.07.) zum Vogelschutz"},
    {"Gewässer": "Wiesent", "Abschnitt": "Oberlauf", "Bundesland": "Bayern", "Typ": "Regulierung", "Status": "Obergrenze: Nur über Mindestpegel frei, organisierter Verleih eingeschränkt"},
    {"Gewässer": "Spreewald", "Abschnitt": "Kernzone Fließe", "Bundesland": "Brandenburg", "Typ": "Sperrung", "Status": "🛑 Temporäre Sperrung wegen Niedrigwasser / Krautung"},
    {"Gewässer": "Rur", "Abschnitt": "Eifel-Abschnitte", "Bundesland": "Nordrhein-Westfalen", "Typ": "Pegelabhängig", "Status": "⚠️ Befahrbar nur bei grünem Pegel (Info über Monschau)"},
    {"Gewässer": "Aller", "Abschnitt": "Mündungsebene", "Bundesland": "Niedersachsen", "Typ": "Umweltwarnung", "Status": "🦠 Blaualgenwarnung! Hautkontakt und Tränken von Hunden vermeiden."},
    {"Gewässer": "Donau", "Abschnitt": "Obere Donau (Naturpark)", "Bundesland": "Baden-Württemberg", "Typ": "Regulierung", "Status": "🛑 Kontingentierung / Befahrungsverbot bei Pegel unter 46cm (Beuron)"},
]

# ==========================================
# DATA FETCHING (LIVE-PEGEL VON PEGELONLINE)
# ==========================================
@st.cache_data(ttl=600)  # Daten werden 10 Minuten im Zwischenspeicher behalten
def load_live_pegel():
    try:
        # Abruf aller Bundeswasserstraßen-Pegel (viele davon für Kanuten an großen Flüssen relevant)
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
    except Exception as e:
        st.error(f"Fehler beim Laden der Live-Pegel: {e}")
    return pd.DataFrame(columns=["Gewässer", "Station", "Pegel (cm)", "Zeitpunkt"])

df_pegel = load_live_pegel()

# ==========================================
# DASHBOARD SIDEBAR (FILTER)
# ==========================================
st.sidebar.header("🗺️ Filter-Optionen")

# Bundesland-Filter
bundeslaender = ["Alle Bundesländer", "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", 
                  "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", 
                  "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]
selected_bl = st.sidebar.selectbox("Wähle ein Bundesland:", bundeslaender)

# Typen-Filter für Sperrungen
info_typ = st.sidebar.multiselect(
    "Informationstyp:", 
    ["Sperrung", "Regulierung", "Umweltschutz", "Pegelabhängig", "Umweltwarnung"],
    default=["Sperrung", "Regulierung", "Umweltschutz", "Pegelabhängig", "Umweltwarnung"]
)

# ==========================================
# HAUPTBEREICH: ANZEIGE
# ==========================================

# Spalten-Layout für die Übersicht
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### ⚠️ Aktuelle Sperrungen & Hinweise für Paddler")
    
    # Filtern der manuellen/erweiterten Datenbank
    df_sperrungen = pd.DataFrame(SPERRUNGEN_DATENBANK)
    
    if selected_bl != "Alle Bundesländer":
        df_sperrungen = df_sperrungen[df_sperrungen["Bundesland"] == selected_bl]
        
    df_sperrungen = df_sperrungen[df_sperrungen["Typ"].isin(info_typ)]
    
    if df_sperrungen.empty:
        st.success("✅ Keine Sperrungen oder Warnungen für die aktuelle Auswahl gemeldet!")
    else:
        for index, row in df_sperrungen.iterrows():
            # Farbe je nach Warnstufe anpassen
            box_type = "error" if "🛑" in row["Status"] else "warning" if "⚠️" in row["Status"] else "info"
            
            with st.expander(f"{row['Status'].split()[0]} {row['Gewässer']} ({row['Abschnitt']}) - {row['Bundesland']}"):
                st.write(f"**Grund/Typ:** {row['Typ']}")
                st.write(f"**Details:** {row['Status']}")
                st.caption(f"Quelle: Manuelle Community-Pflege / Landesamt • Stand: {datetime.now().strftime('%d.%m.%Y')}")

with col2:
    st.markdown("### 🌊 Bundesweite Live-Pegelstände (Hauptflüsse)")
    
    # Filter für Pegel nach Gewässer-Suchbegriff
    search_river = st.text_input("🔍 Pegel nach Flussnamen filtern (z.B. Donau, Rhein, Isar):", "")
    
    df_pegel_filtered = df_pegel.copy()
    if search_river:
        df_pegel_filtered = df_pegel_filtered[df_pegel_filtered["Gewässer"].str.contains(search_river, case=False, na=False)]
    
    if df_pegel_filtered.empty:
        st.info("Keine Pegelstationen für diesen Suchbegriff gefunden.")
    else:
        st.dataframe(
            df_pegel_filtered.sort_values(by="Gewässer"), 
            use_container_width=True, 
            hide_index=True
        )

# INFOTEXT FÜR NUTZER
st.markdown("---")
st.info("💡 **Hinweis für Kanuten:** Dieses Dashboard kombiniert automatisierte Echtzeit-Daten des Bundes (Pegelonline) mit regionalen Umwelt- und Befahrungsregeln. Vor Fahrtantritt wird immer ein Blick auf die lokalen Pegel der Kreisverwaltungen empfohlen.")
