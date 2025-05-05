import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import requests
from io import StringIO
import matplotlib.pyplot as plt

# --- API seaded ---
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
        "values": ["2", "3"]  # 2=Mees, 3=Naine
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

# --- Geoandmete laadimine Google Drive'ist ---
@st.cache_data
def load_geojson():
    url = "https://drive.google.com/uc?export=download&id=15PWvqdxtp6HHIQIftsmHl4pMmWvG8mQX"
    return gpd.read_file(url)

# --- Rakenduse töö ---
st.title("Loomulik iive Eesti maakondades")
st.markdown("Visualiseeri loomulik iive aastate lõikes Statistikaameti andmete põhjal.")

# Lae andmed
df = import_data()
gdf = load_geojson()

# Aasta valik
valikud = sorted(df["Aasta"].unique())
valitud_aasta = st.sidebar.selectbox("Vali aasta", valikud)

# Filtreeri valitud aasta
df_aasta = df[df["Aasta"] == valitud_aasta]

# Pivot tabel: Mehed + Naised
df_pivot = df_aasta.pivot_table(
    index="Maakond", columns="Sugu", values="Loomulik iive", aggfunc="sum"
).reset_index()

# Lisa summaveerg
df_pivot["Loomulik iive"] = df_pivot[2] + df_pivot[3]

# Ühenda GeoJSON-iga
merged = gdf.merge(df_pivot, left_on="MNIMI", right_on="Maakond")

# --- Visualiseeri kaart ---
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

# Kuvame joonise Streamlitis
st.pyplot(fig)
