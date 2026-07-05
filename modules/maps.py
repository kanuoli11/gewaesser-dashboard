import folium
from streamlit_folium import st_folium


def create_base_map():
    """
    Zentrale Deutschland-Karte
    """
    return folium.Map(
        location=[51.2, 10.5],
        zoom_start=6,
        tiles="OpenStreetMap"
    )


def add_dummy_points(m):
    """
    Platzhalterpunkte (später echte Geodaten)
    """
    folium.Marker(
        [51.5, 7.4],
        tooltip="Beispiel: NRW Pegel"
    ).add_to(m)

    folium.Marker(
        [48.1, 11.5],
        tooltip="Beispiel: Bayern Sperrung"
    ).add_to(m)

    return m
