import requests
import pandas as pd
import streamlit as st

@st.cache_data(ttl=600)
def load_pegel():
    """
    Lädt Live-Pegelstände von PEGELONLINE (WSV)
    """
    headers = {"User-Agent": "Mozilla/5.0 (KanuPortal Dashboard)"}
    try:
        url = "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json?includeCurrentMeasurement=true"
        r = requests.get(url, headers=headers, timeout=15)
        data = []
        if r.status_code == 200:
            stations = r.json()
            for s in stations:
                if "currentMeasurement" in s:
                    data.append({
                        "Gewässer": s.get("water", {}).get("shortname", "Unbekannt"),
                        "Station": s.get("name"),
                        "Pegel": s["currentMeasurement"].get("value"),
                        "Zeit": s["currentMeasurement"].get("timestamp")
                    })
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"Pegeldaten konnten nicht geladen werden: {e}")
        return pd.DataFrame(columns=["Gewässer", "Station", "Pegel", "Zeit"])
