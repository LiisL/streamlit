import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import requests
from io import StringIO
import matplotlib.pyplot as plt
import tempfile
import os

# --- Statistikaameti API seaded ---
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"

JSON_PAYLOAD = {
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [str(aasta) for aasta in range(2014, 2024)]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39", "44", "49", "51", "57", "59", "65", "67", "70",
          "74", "78", "82", "84", "86"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2", "3"]  # 2=Mehed, 3=Naised
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}

# --- Andmete laadimine Statistikaametist ---
@st.cache_data
def import_data():
    response = requests.post(STATISTIKAAMETI_API_URL, json=JSON_PAYLOAD)
    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"API viga: {response.status_code}")
        return pd.DataFrame()

# --- GeoJSON fail Google Drive'ist ---
@st.cache_data
def load_geojson():
    url = "https://drive.google.com/uc?export=download&id=15PWvqdxtp6HHIQIftsmHl4pMmWvG8mQX"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("Ei suutnud GeoJSON faili Google Drive'ist alla laadida.")
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmp_file:
        tmp_file.write(response.content)
        tmp_path = tmp_file.name

    gdf = gpd.read_file(tmp_path)
    os.remove(tmp_path)
    return gdf

# --- Streamlit rakendus ---
st.title("Loomulik iive Eesti maakondades")
st.markdown("Visualiseeri loomulik iive aastate lõikes Statistikaameti andmete põhjal.")

# Lae andmed
df = import_data()
gdf = load_geojson()

# Aasta valik
aastad = sorted(df["Aasta"].unique())
valitud_aasta = st.sidebar.selectbox("Vali aasta", aastad)

# Filtreeri andmed
df_aasta = df[df["Aasta"] == valitud_aasta]

# Pivot: liida meeste ja naiste loomulik iive
df_pivot = df_aasta.pivot_table(
    index="Maakond", columns="Sugu", values="Loomulik iive", aggfunc="sum"
).reset_index()
df_pivot["Loomulik iive"] = df_pivot[2] + df_pivot[3]

# Ühenda ruumiandmetega
merged = gdf.merge(df_pivot, left_on="MNIMI", right_on="Maakond")

# --- Visualiseerimine ---
fig, ax = plt.subplots(figsize=(8, 6))
merged.plot(
    column="Loomulik iive",
    cmap="RdYlGn",
    linewidth=0.8,
    edgecolor="0.8",
    legend=True,
    ax=ax
)
ax.set_title(f"Loomulik iive maakondade kaupa - {valitud_aasta}", fontsize=14)
ax.axis("off")
st.pyplot(fig)
