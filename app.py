import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
import plotly.express as px


# ============================================================
# Configuration
# ============================================================

st.set_page_config(
    page_title="Navigation administrative Maroc",
    page_icon="🌍",
    layout="wide"
)


# ============================================================
# Charger les shapefiles
# ============================================================

regions = gpd.read_file("data/Regions_WGS84.shp")
provinces = gpd.read_file("data/Provinces_WGS84.shp")
communes = gpd.read_file("data/communes_WGS84.shp")

# S'assurer que les couches sont en WGS84
regions = regions.to_crs(epsg=4326)
provinces = provinces.to_crs(epsg=4326)
communes = communes.to_crs(epsg=4326)


# ============================================================
# Titre
# ============================================================

st.title("🌍 Navigation administrative Maroc")


# ============================================================
# Colonnes attributaires
# ============================================================

REGION_COL = "libelle_fr"
REGION_IN_COMMUNE = "FIRST_regi"
PROVINCE_COL = "FIRST_prov"
COMMUNE_COL = "FIRST_com_"


# ============================================================
# Initialisation des variables
# ============================================================

selected_region = ""
selected_province = ""
selected_communes = ""

provinces_filtrees = None
communes_filtrees = None


# ============================================================
# MODULE 1 : Navigation administrative
# ============================================================

st.header("🧭 Module 1 : Navigation administrative")

# Menu Région
region_names = sorted(regions[REGION_COL].dropna().unique())

selected_region = st.selectbox(
    "Choisir une région",
    [""] + list(region_names)
)

# Menu Province
if selected_region != "":
    provinces_filtrees = communes[
        communes[REGION_IN_COMMUNE] == selected_region
    ]

    province_names = sorted(
        provinces_filtrees[PROVINCE_COL].dropna().unique()
    )

    selected_province = st.selectbox(
        "Choisir une province",
        [""] + list(province_names)
    )

# Menu Commune
if selected_province != "":
    communes_filtrees = provinces_filtrees[
        provinces_filtrees[PROVINCE_COL] == selected_province
    ]

    commune_names = sorted(
        communes_filtrees[COMMUNE_COL].dropna().unique()
    )

    selected_communes = st.selectbox(
        "Choisir une commune",
        [""] + list(commune_names)
    )


# ============================================================
# MODULE 2 : Mode d'affichage cartographique
# ============================================================

st.header("🗺️ Module 2 : Visualisation cartographique")

mode_affichage = st.radio(
    "Choisir le mode d'affichage",
    [
        "Contour seulement",
        "Contour + MNT",
        "MNT seulement"
    ]
)


# ============================================================
# Déterminer l'entité active
# ============================================================

active_gdf = None
active_level = None
active_name = None

# Cas 1 : Région seulement
if selected_region != "" and selected_province == "":
    active_level = "Région"
    active_name = selected_region

    active_gdf = regions[
        regions[REGION_COL] == selected_region
    ]

# Cas 2 : Province
elif selected_region != "" and selected_province != "" and selected_communes == "":
    active_level = "Province"
    active_name = selected_province

    communes_province = communes[
        (communes[REGION_IN_COMMUNE] == selected_region) &
        (communes[PROVINCE_COL] == selected_province)
    ].copy()

    # Fusion des communes pour avoir le contour de la province
    geom_fusionnee = communes_province.geometry.union_all()

    active_gdf = gpd.GeoDataFrame(
        {"nom": [selected_province]},
        geometry=[geom_fusionnee],
        crs=communes.crs
    )

# Cas 3 : Commune
elif selected_region != "" and selected_province != "" and selected_communes != "":
    active_level = "Commune"
    active_name = selected_communes

    active_gdf = communes[
        (communes[REGION_IN_COMMUNE] == selected_region) &
        (communes[PROVINCE_COL] == selected_province) &
        (communes[COMMUNE_COL] == selected_communes)
    ]


# Si aucune entité n'est sélectionnée
if active_gdf is None or active_gdf.empty:
    st.info("👈 Sélectionne une région pour afficher la carte.")
    st.stop()


# Nettoyer les géométries nulles
active_gdf = active_gdf[active_gdf.geometry.notnull()]


# ============================================================
# Calcul du centre et de l'emprise
# ============================================================

geom_union = active_gdf.geometry.union_all()
centre = geom_union.representative_point()

lon = centre.x
lat = centre.y

bounds = active_gdf.total_bounds
minx, miny, maxx, maxy = bounds


# ============================================================
# Titre de l'entité sélectionnée
# ============================================================

if selected_communes != "":
    titre = f"{selected_region} / {selected_province} / {selected_communes}"
elif selected_province != "":
    titre = f"{selected_region} / {selected_province}"
else:
    titre = f"{selected_region}"

st.subheader(f"📍 Entité sélectionnée : {titre}")


# ============================================================
# Création de la carte
# ============================================================

m = folium.Map(
    location=[lat, lon],
    zoom_start=7,
    tiles="OpenStreetMap",
    control_scale=True
)


# ============================================================
# Ajouter le MNT
# ============================================================

if mode_affichage in ["Contour + MNT", "MNT seulement"]:
    folium.raster_layers.WmsTileLayer(
        url="https://ows.terrestris.de/osm/service",
        layers="SRTM30-Colored-Hillshade",
        name="MNT Terrestris SRTM",
        fmt="image/png",
        transparent=True,
        overlay=True,
        control=True,
        opacity=0.6,
        attr="Terrestris SRTM"
    ).add_to(m)


# ============================================================
# Ajouter le contour
# ============================================================

if mode_affichage in ["Contour seulement", "Contour + MNT"]:
    folium.GeoJson(
        active_gdf,
        name=f"Contour {active_level}",
        style_function=lambda x: {
            "fillOpacity": 0,
            "fillColor": "transparent",
            "color": "blue",
            "weight": 3
        },
        popup=f"{active_level} : {active_name}"
    ).add_to(m)


# ============================================================
# Recadrage automatique sur l'entité
# ============================================================

m.fit_bounds([
    [miny, minx],
    [maxy, maxx]
])


# Contrôle des couches
folium.LayerControl().add_to(m)


# ============================================================
# Affichage de la carte
# ============================================================

st_folium(
    m,
    width=1000,
    height=600,
    key=f"map_{active_level}_{active_name}_{mode_affichage}"
)

st.caption("Contour bleu : entité administrative sélectionnée.")
st.caption("MNT : Modèle Numérique de Terrain chargé depuis Terrestris WMS.")


# ============================================================
# MODULE 3 : Données climatiques prévisionnelles
# ============================================================

st.header("🌦️ Module 3 : Données climatiques prévisionnelles")

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": lat,
    "longitude": lon,
    "daily": "temperature_2m_max,precipitation_sum",
    "timezone": "auto",
    "forecast_days": 15
}

response = requests.get(url, params=params)

if response.status_code != 200:
    st.error("Erreur lors de la récupération des données météo.")
    st.stop()

data = response.json()

if "daily" not in data:
    st.error("Les données météo ne sont pas disponibles.")
    st.stop()


# ============================================================
# Création du DataFrame météo
# ============================================================

date = data["daily"]["time"]
temperature = data["daily"]["temperature_2m_max"]
precipitation = data["daily"]["precipitation_sum"]

df = pd.DataFrame({
    "date": date,
    "temperature": temperature,
    "precipitation": precipitation
})


# ============================================================
# Indicateurs météo
# ============================================================

moy_temp = df["temperature"].mean()
max_temp = df["temperature"].max()
total_pluie = df["precipitation"].sum()

st.metric("Température moyenne", f"{moy_temp:.1f} °C")
st.metric("Température maximale", f"{max_temp:.1f} °C")
st.metric("Précipitations cumulées", f"{total_pluie:.1f} mm")


# ============================================================
# MODULE 4 : Visualisation temporelle
# ============================================================

st.header("📊 Module 4 : Visualisation temporelle")

parametre = st.radio(
    "Choisir le paramètre",
    ["Température", "Précipitations"]
)

df["date"] = pd.to_datetime(df["date"])
df["date"] = df["date"].dt.strftime("%d/%m/%Y")


# ============================================================
# Graphique température ou précipitations
# ============================================================

if parametre == "Température":
    fig = px.line(
        df,
        x="date",
        y="temperature",
        title=f"🌡️ Température maximale sur 15 jours - {titre}",
        labels={
            "date": "Date",
            "temperature": "Température (°C)"
        },
        markers=True
    )

    fig.update_traces(
        line=dict(color="red", width=3),
        marker=dict(size=7)
    )

else:
    fig = px.bar(
        df,
        x="date",
        y="precipitation",
        title=f"🌧️ Précipitations cumulées sur 15 jours - {titre}",
        labels={
            "date": "Date",
            "precipitation": "Précipitations (mm)"
        }
    )

    fig.update_traces(
        marker_color="royalblue"
    )


fig.update_layout(
    hovermode="x unified",
    xaxis_title="Date",
    yaxis_title="Valeur",
    margin=dict(l=20, r=20, t=60, b=30)
)

st.plotly_chart(fig, use_container_width=True)

