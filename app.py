import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
import plotly.express as px



## Charger les shapefiles
regions = gpd.read_file("D:\python\data\Regions_WGS84.shp")
provinces = gpd.read_file("D:\python\data\Provinces_WGS84.shp")
communes = gpd.read_file("D:\python\data\communes_WGS84.shp")

st.title(" 🌍 Navigation administrative Maroc")

#ON DIVISE L'INTERFACE PAR 3 COLLONES
col1, col2, col3 = st.columns([1, 2, 1.5])

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
liste_regions = regions[REGION_COL].unique()

selected_region = st.selectbox(
    "Choisir une région",[""] + list(regions["libelle_fr"].unique())
)

if selected_region != "":
#filtre les provinces de la region choisie
    provinces_filtrees = communes[
        communes[REGION_IN_COMMUNE] == selected_region
    ]

#MENU PROVINCES
    liste_provinces = list(provinces_filtrees[PROVINCE_COL].unique())

    selected_province = st.selectbox( 
        "Choisir une province", [""] + liste_provinces
    )

#filtre les communes de la region choisie
    if selected_province != "" :
        communes_filtrees = provinces_filtrees[
        provinces_filtrees["FIRST_prov"] == selected_province
    ]

#MENU COMMUNES
        liste_communes = list(communes_filtrees[COMMUNE_COL].unique())

        selected_communes = st.selectbox(
            "Choisir une commune", [""] + 
            liste_communes
        )

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
active_gdf = None 

if selected_region != "" and selected_province == "":
# région
    active_gdf = regions[
        regions["libelle_fr"] == selected_region
    ]


elif selected_province != "" and selected_communes == "":
# province (à partir communes)
    active_gdf = communes[
        (communes["FIRST_regi"] == selected_region) &
        (communes["FIRST_prov"] == selected_province)
    ].dissolve()


elif selected_communes != "":
# commune
    active_gdf = communes[
        (communes["FIRST_regi"] == selected_region) &
        (communes["FIRST_prov"] == selected_province) &
        (communes["FIRST_com_"] == selected_communes)
    ]
## Verifier qu'une entite est selectionnee


if active_gdf is None or active_gdf.empty:
    st.info("Sélectionne une région pour afficher la carte.")
    st.stop()

# calcul du centre
centre = active_gdf.geometry.union_all().centroid

lat = centre.y
lon = centre.x

# Creation de la carte
m = folium.Map(location=[lat, lon], zoom_start=7, control_scale = True, tiles =  "OpenStreetMap")

# nettoyer données
active_gdf = active_gdf[active_gdf.geometry.notnull()]

# fusion
geom_union = active_gdf.geometry.union_all()

# MODE 1 : Contour + MNT
if mode_affichage == "Contour + MNT":

    folium.GeoJson(
        active_gdf,
        name="Contour",
        style_function=lambda x: {
            "fillOpacity": 0,   
            "color": "blue",       
            "weight": 3
        }
    ).add_to(m)

    folium.raster_layers.WmsTileLayer(
        url="https://ows.terrestris.de/osm/service?",
        layers="SRTM30-Colored-Hillshade",   
        name="MNT Terrestris",
        fmt="image/png",
        transparent=True,
        overlay=True,
        control=True
    ).add_to(m)

# MODE 2 : MNT seulement
elif mode_affichage == "MNT seulement":

    folium.raster_layers.WmsTileLayer(
        url="https://ows.terrestris.de/osm/service?",
        layers="SRTM30-Colored-Hillshade",   
        name="MNT Terrestris",
        fmt="image/png",
        transparent=True,
        overlay=True,
        control=True
    ).add_to(m)

# MODE 3 : CONTOUR SEULEMENT
elif mode_affichage == "Contour seulement":

    folium.GeoJson(
        active_gdf,
        name="Contour",
        style_function=lambda x: {
            "fillOpacity": 0,   
            "color": "blue",       
            "weight": 3
        }
    ).add_to(m)

bounds = active_gdf.total_bounds   # [minx, miny, maxx, maxy]
m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

## TITRE
if "selected_communes" in locals():
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