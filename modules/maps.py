import folium

def create_base_map():
    return folium.Map(
        location=[51.2, 10.5],
        zoom_start=6,
        tiles="OpenStreetMap"
    )

def add_dummy_points(m):
    folium.CircleMarker(
        location=[51.5, 7.4],
        radius=10,
        color="#0d6efd",
        fill=True,
        fill_color="#0d6efd",
        fill_opacity=0.9,
        tooltip="Beispiel: NRW Pegel"
    ).add_to(m)

    folium.CircleMarker(
        location=[48.1, 11.5],
        radius=10,
        color="#d62828",
        fill=True,
        fill_color="#d62828",
        fill_opacity=0.9,
        tooltip="Beispiel: Bayern Sperrung"
    ).add_to(m)

    return m
