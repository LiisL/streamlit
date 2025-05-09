import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import requests
import tempfile
import os
import json
from io import StringIO

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"

JSON_PAYLOAD_STR ="""{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": ["2014","2015","2016","2017","2018","2019","2020","2021","2022","2023"]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "001", "37", "39", "44", "49", "51", "57", "59", "65", "67",
          "70", "74", "78", "82", "84", "86"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2","3"]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}"""

@st.cache_data
def import_data():
    headers = {'Content-Type': 'application/json'}
    payload = json.loads(JSON_PAYLOAD_STR)
    response = requests.post(STATISTIKAAMETI_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"API error {response.status_code}")
        return pd.DataFrame()

@st.cache_data
def load_geojson():
    url = "https://drive.google.com/uc?export=download&id=15PWvqdxtp6HHIQIftsmHl4pMmWvG8mQX"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Ei suutnud geoandmeid alla laadida.")
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmp_file:
        tmp_file.write(response.content)
        tmp_path = tmp_file.name
    gdf = gpd.read_file(tmp_path)
    os.remove(tmp_path)
    return gdf

# --- Streamlit ---
st.title("Loomulik iive Eesti maakondades")
# ---st.markdown("Visualiseeri loomulik iive aastate lõikes Statistikaameti andmete põhjal.")---

df = import_data()
gdf = load_geojson()

if df.empty or gdf is None:
    st.stop()

df.columns = df.columns.str.strip()

# Aastavalik
aastad = sorted(df["Aasta"].unique())
valitud_aasta = st.sidebar.selectbox("Vali aasta", aastad)
df_aasta = df[df["Aasta"] == valitud_aasta]

# Veerukontroll
required_cols = {"Mehed Loomulik iive", "Naised Loomulik iive", "Maakond"}
if not required_cols.issubset(df_aasta.columns):
    st.error(f"Puuduvad vajalikud veerud: {required_cols - set(df_aasta.columns)}")
    st.write("Veerud:", df_aasta.columns.tolist())
    st.stop()

# Arvuta loomulik iive
df_aasta["Loomulik iive"] = df_aasta["Mehed Loomulik iive"] + df_aasta["Naised Loomulik iive"]
df_pivot = df_aasta[["Maakond", "Loomulik iive"]]

# Teisenda maakonnanimed sobivaks GeoJSON-iga
nimi_asendused = {
    "Harjumaa": "Harju maakond",
    "Hiiumaa": "Hiiu maakond",
    "Ida-Virumaa": "Ida-Viru maakond",
    "Järvamaa": "Järva maakond",
    "Jõgevamaa": "Jõgeva maakond",
    "Läänemaa": "Lääne maakond",
    "Lääne-Virumaa": "Lääne-Viru maakond",
    "Põlvamaa": "Põlva maakond",
    "Pärnumaa": "Pärnu maakond",
    "Raplamaa": "Rapla maakond",
    "Saaremaa": "Saare maakond",
    "Tartumaa": "Tartu maakond",
    "Valgamaa": "Valga maakond",
    "Viljandimaa": "Viljandi maakond",
    "Võrumaa": "Võru maakond",
    "Tallinn": "Harju maakond"
}
df_pivot["Maakond"] = df_pivot["Maakond"].replace(nimi_asendused)

# Ühenda ruumiandmetega
merged = gdf.merge(df_pivot, left_on="MNIMI", right_on="Maakond")

# Kaart koos legendi sildiga
fig, ax = plt.subplots(figsize=(8, 6))
merged.plot(
    column="Loomulik iive",
    cmap="RdYlGn",
    linewidth=0.8,
    edgecolor="0.8",
    legend=True,
    legend_kwds={"label": "Loomulik iive"},  # ← See rida lisab sildi legendile
    ax=ax
)
ax.set_title(f"Loomulik iive maakondade kaupa – {valitud_aasta}", fontsize=14)
ax.axis("off")
st.pyplot(fig)

