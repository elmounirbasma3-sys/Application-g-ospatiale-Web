import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
import plotly.express as px
import json

## Charger les shapefiles


with open("data/regions.geojson") as f:
    regions = json.load(f)

with open("data/provinces.geojson") as f:
    provinces = json.load(f)

with open("data/communes.geojson") as f:
    communes = json.load(f)



st.title(" 🌍 Navigation administrative Maroc")


#Lecture

#st.write(regions)
#st.write(provinces)
#st.write(communes)

REGION_COL = "libelle_fr"
REGION_IN_COMMUNE = "FIRST_regi"
PROVINCE_COL = "FIRST_prov"
COMMUNE_COL = "FIRST_com_"

selected_province = ""
selected_communes = ""
provinces_filtrees = None
communes_filtrees = None

# MODULE 1 : Module de navigation administrative ------------------------------------------------------------------------------------

#MENU REGION

region_names = sorted(list(set(
    feat["properties"]["libelle_fr"]
    for feat in regions["features"]
    if feat["properties"].get("libelle_fr")
)))

selected_region = st.selectbox("Choisir une région", [""] + region_names)

# === FILTRAGE COMMUNES ===
filtered_features = []

if selected_region != "":
    filtered_features = [
        f for f in communes["features"]
        if f["properties"].get("FIRST_regi") == selected_region
    ]


# MODULE 2 : Module de visualisation cartographique ---------------------------------------------------------------------------------------


mode_affichage = st.radio(
    "Choisir le mode d'affichage",
    [
        "Contour seulement",
        "Contour + MNT",
        "MNT seulement",
    ]
)


##Determiner l'entite active

# === CENTRE PAR DEFAUT
lat, lon = 31.7917, -7.0926

# === CENTRE SI FILTRAGE
if filtered_features:
    coords = filtered_features[0]["geometry"]["coordinates"]
    try:
        lon = coords[0][0][0]
        lat = coords[0][0][1]
    except:
        pass

# === CREATION CARTE
# === CREATION CARTE
m = folium.Map(location=[lat, lon], zoom_start=6)

geo = {
    "type": "FeatureCollection",
    "features": filtered_features if filtered_features else regions["features"]
}

if mode_affichage in ["Contour seulement", "Contour + MNT"]:
    folium.GeoJson(
        geo,
        style_function=lambda x: {
            "fillOpacity": 0,
            "color": "blue",
            "weight": 2
        }
    ).add_to(m)

if mode_affichage in ["Contour + MNT", "MNT seulement"]:
    folium.raster_layers.WmsTileLayer(
        url="https://ows.terrestris.de/osm/service?",
        layers="SRTM30-Colored-Hillshade",
        fmt="image/png",
        transparent=True,
        overlay=True
    ).add_to(m)


## TITRE
if selected_communes != "" :
    titre = f"{selected_region} / {selected_province} / {selected_communes}"
elif selected_province != "":
    titre = f"{selected_region} / {selected_province}"
else:
    titre = f"{selected_region}"

st.markdown(f"### 📍 {titre}")

##AFFICHAGE
st_folium(m, width = 900 , height = 500 )


### MODULE 3 : Module de données climatiques prévisionnelles ---------------------------------------------------------------
## REQUETE API
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": lat,
    "longitude": lon,
    "daily": "temperature_2m_max,precipitation_sum",
    "timezone": "auto",
    "forecast_days" : 15
}


response = requests.get(url, params=params)
data = response.json()


### MODULE 4 : Module de visualisation temporelle -------------------------------------------------------------
## CREATION DES DONNEES

date = data["daily"]["time"]
temperature = data["daily"]["temperature_2m_max"]
precipitation  = data["daily"]["precipitation_sum"]

df = pd.DataFrame({
    "date": date,
    "temperature": temperature ,
    "precipitation": precipitation
})


moy_temp = df["temperature"].mean()
max_temp = df["temperature"].max()
total_pluie = df["precipitation"].sum()



## DEMANDER A L'UTILISATEUR DE CHOISIR UN CHOIX 

parametre = st.radio(
    "Choisir le paramètre",
    ["Température", "Précipitations"]
)


df["date"]= pd.to_datetime(df["date"])
df["date"] = df["date"].dt.strftime("%d/%m/%Y")

## AFFICHER LE GRAPHIQUE 


if parametre == "Température":

    fig = px.line(
        df,
        x="date",
        y="temperature",
        title=f"🌡️ Température (°C) - {titre}",
        labels={
        "date": "Date",
            "temperature": "Température (°C)"
        }
    )



else:
    fig = px.bar(
        df,
        x="date",
        y="precipitation",
        title=f"🌧️ Précipitations (mm) - {titre}",
        labels={
            "date": "Date",
            "precipitation": "Précipitations (mm)"
        }
    )




if parametre == "Température":
    fig.update_traces(
        line=dict(color="#6366F1", width=3),
        marker=dict(size=7, color="#F43F5E")
    )
else:
    fig.update_traces(
        marker_color="#38BDF8"
    )
st.plotly_chart(fig, use_container_width=True)
