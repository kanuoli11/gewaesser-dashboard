import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date

# SPRECHENDE TITEL UND LAYOUT EINRICHTEN
st.set_page_config(page_title="Kanu- & Paddel-Dashboard Deutschland", layout="wide", page_icon="🛶")

st.title("🛶 Bundesweites Kanu- & Paddel-Dashboard")
st.subheader("Echtzeit-Pegel, Befahrungsregelungen, Sperrungen und Umweltwarnungen für ganz Deutschland")

# ==========================================
# KONFIGURATION: DATENBANK MIT ABLAUFDATUM
# ==========================================
# WICHTIG: Das Datum muss immer im Format "JJJJ-MM-TT" eingetragen werden.
# Wenn eine Meldung kein festes Ablaufdatum hat, setze es weit in die Zukunft (z.B. "2030-12-31").

SPERRUNGEN_DATENBANK = [
    {
        "Gewässer": "Isar", 
        "Abschnitt": "Freising bis Landshut", 
        "Bundesland": "Bayern", 
        "Typ": "Umweltschutz", 
        "Status": "⚠️ Befahrungsverbot zum Vogelschutz (jährlich von März bis Ende Juli).",
        "Gültig_bis": "2026-07-31"
    },
    {
        "Gewässer": "Wiesent", 
        "Abschnitt": "Oberlauf", 
        "Bundesland": "Bayern", 
        "Typ": "Regulierung", 
        "Status": "Obergrenze: Nur über Mindestpegel frei, organisierter Verleih eingeschränkt.",
        "Gültig_bis": "2026-10-31"
    },
    {
        "Gewässer": "Spreewald", 
        "Abschnitt": "Kernzone Fließe", 
        "Bundesland": "Brandenburg", 
        "Typ": "Sperrung", 
        "Status": "🛑 Temporäre Sperrung wegen Niedrigwasser / Krautung.",
        "Gültig_bis": "2026-06-15"  # Diese Meldung rutscht automatisch ins Archiv!
    },
    {
        "Gewässer": "Rur", 
        "Abschnitt": "Eifel-Abschnitte", 
        "Bundesland": "Nordrhein-Westfalen", 
        "Typ": "Pegelabhängig", 
        "Status": "⚠️ Befahrbar nur bei grünem Pegel (Info über Monschau).",
        "Gültig_bis": "2027-12-31"
    },
    {
        "Gewässer": "Aller", 
        "Abschnitt": "Mündungsebene", 
        "Bundesland": "Niedersachsen", 
        "Typ": "Umweltwarnung", 
        "Status": "🦠 Blaualgenwarnung! Hautkontakt und Tränken von Hunden vermeiden.",
        "Gültig_bis": "2026-09-15"
    },
    {
        "Gewässer": "Donau", 
        "Abschnitt": "Obere Donau (Naturpark)", 
        "Bundesland": "Baden-Württemberg", 
        "Typ": "Regulierung", 
        "Status": "🛑 Kontingentierung / Befahrungsverbot bei Pegel unter 46cm (Beuron).",
        "Gültig_bis": "2028-01-01"
    },
]

# ==========================================
# DATA FETCHING (LIVE-PEGEL VON PEGELONLINE)
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
    except Exception as e:
        st.error(f"Fehler beim Laden der Live-Pegel: {e}")
    return pd.DataFrame(columns=["Gewässer", "Station", "Pegel (cm)", "Zeitpunkt"])

df_pegel = load_live_pegel()

# ==========================================
# DASHBOARD SIDEBAR (FILTER)
# ==========================================
st.sidebar.header("🗺️ Filter-Optionen")

bundeslaender = ["Alle Bundesländer", "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", 
                  "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", 
                  "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]
selected_bl = st.sidebar.selectbox("Wähle ein Bundesland:", bundeslaender)

info_typ = st.sidebar.multiselect(
    "Informationstyp:", 
    ["Sperrung", "Regulierung", "Umweltschutz", "Pegelabhängig", "Umweltwarnung"],
    default=["Sperrung", "Regulierung", "Umweltschutz", "Pegelabhängig", "Umweltwarnung"]
)

# ==========================================
# DATEN VERARBEITEN (AKTUELL VS. ARCHIV)
# ==========================================
heute = date.today()
aktive_meldungen = []
archiv_meldungen = []

for meldung in SPERRUNGEN_DATENBANK:
    # Datumstext in ein echtes Datum umwandeln, um es vergleichen zu können
    ablauf_datum = datetime.strptime(meldung["Gültig_bis"], "%Y-%m-%d").date()
    
    if ablauf_datum >= heute:
        aktive_meldungen.append(meldung)
    else:
        archiv_meldungen.append(meldung)

df_aktiv = pd.DataFrame(aktive_meldungen) if aktive_meldungen else pd.DataFrame(columns=["Gewässer", "Abschnitt", "Bundesland", "Typ", "Status", "Gültig_bis"])
df_archiv = pd.DataFrame(archiv_meldungen) if archiv_meldungen else pd.DataFrame(columns=["Gewässer", "Abschnitt", "Bundesland", "Typ", "Status", "Gültig_bis"])

# Filter auf die Daten anwenden
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
    st.markdown("### ⚠️ Aktuelle Sperrungen & Hinweise")
    
    if df_aktiv.empty:
        st.success("✅ Keine aktiven Sperrungen oder Warnungen für die aktuelle Auswahl gemeldet!")
    else:
        for index, row in df_aktiv.iterrows():
            box_type = "error" if "🛑" in row["Status"] else "warning" if "⚠️" in row["Status"] else "info"
            
            with st.expander(f"{row['Status'].split()[0] if row['Status'].split() else ''} {row['Gewässer']} ({row['Abschnitt']}) - {row['Bundesland']}"):
                st.write(f"**Grund/Typ:** {row['Typ']}")
                st.write(f"**Details:** {row['Status']}")
                # Schönes deutsches Datum für die Anzeige formatieren
                ziel_datum = datetime.strptime(row["Gültig_bis"], "%Y-%m-%d").strftime("%d.%m.%Y")
                st.caption(f"Diese Meldung wird automatisch angezeigt bis: {ziel_datum}")

    # ARCHIV-BEREICH WEITER UNTEN IN SPALTE 1
    st.markdown("---")
    st.markdown("### 📂 Archiv: Kürzlich abgelaufene Infos")
    with st.get_container():
        if df_archiv.empty:
            st.caption("Keine abgelaufenen Meldungen im Archiv für diese Auswahl.")
        else:
            for index, row in df_archiv.iterrows():
                with st.expander(f"⚪ [ABGELAUFEN] {row['Gewässer']} ({row['Abschnitt']})"):
                    st.write(f"**Ehemaliger Status:** {row['Status']}")
                    alt_datum = datetime.strptime(row["Gültig_bis"], "%Y-%m-%d").strftime("%d.%m.%Y")
                    st.caption(f"Gültigkeit lief ab am: {alt_datum}")

with col2:
    st.markdown("### 🌊 Bundesweite Live-Pegelstände (Hauptflüsse)")
    
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

st.markdown("---")
st.info("💡 **Hinweis für Kanuten:** Dieses Dashboard kombiniert automatisierte Echtzeit-Daten des Bundes (Pegelonline) mit regionalen Umwelt- und Befahrungsregeln. Vor Fahrtantritt wird immer ein Blick auf die lokalen Pegel der Kreisverwaltungen empfohlen.")
