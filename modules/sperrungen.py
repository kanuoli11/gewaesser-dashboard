import json
from pathlib import Path
from datetime import datetime, date
import pandas as pd

def split_sperrungen(sp_list):
    """
    Trennt Sperrungen in aktiv und archiviert
    """
    heute = date.today()

    aktiv = []
    archiv = []

    for s in sp_list:
        try:
            gueltig_bis = datetime.strptime(s["Gültig_bis"], "%Y-%m-%d").date()

            if gueltig_bis >= heute:
                aktiv.append(s)
            else:
                archiv.append(s)

        except:
            # Falls Datum kaputt ist -> sicherheitshalber aktiv anzeigen
            aktiv.append(s)

    return aktiv, archiv


def filter_sperrungen(sp_list, bundesland=None, typ_filter=None):
    """
    Filtert Sperrungen nach Bundesland und Typ
    """

    df = pd.DataFrame(sp_list)

    if df.empty:
        return df

    if bundesland and bundesland != "Alle":
        df = df[df["Bundesland"] == bundesland]

    if typ_filter:
        df = df[df["Typ"].isin(typ_filter)]

    return df
