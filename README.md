*** Navigation Administrative & Données Climatiques ***

** Description du projet
Cette application interactive développée avec Streamlit permet de naviguer à travers les divisions administratives du Maroc (régions, provinces, communes) et de visualiser :

- Les limites géographiques (cartographie)
- Le relief (MNT - Modèle Numérique de Terrain)
- Les données climatiques prévisionnelles (température et précipitations)

> L’utilisateur peut sélectionner une zone géographique et explorer ses caractéristiques sous forme de carte et de graphiques.

** Fonctionnalités principales
 1. Navigation administrative

-Sélection d'une région
-Filtrage automatique des provinces
-Sélection d'une commune


 2. Visualisation cartographique (Folium)
3 modes d'affichage :

- Contour seulement
- Contour + MNT (relief)
- MNT seulement

Fonctionnalités :

Zoom automatique sur la zone sélectionnée
Affichage des limites administratives
Superposition du relief


 3. Données climatiques (API Open-Meteo)

Données prévisionnelles sur 15 jours
Paramètres :

Température maximale 
Précipitations 

 4. Visualisation temporelle (Plotly)
Graphique dynamique :
 - Température (courbe)
 - Précipitations (barres)

Indicateurs calculés :
 - Température moyenne
 - Température maximale
 - Cumul des précipitations

Sources de données : Données géographiques

Shapefiles des divisions administratives du Maroc :
 - Régions
 - Provinces
 - Communes

Format : .shp (GeoPandas)

Données climatiques : API Open-Meteo
Lien : https://api.open-meteo.com/v1/forecast

Relief (MNT)
Service WMS : https://ows.terrestris.de/osm/service?

** Technologies utilisées

- Python 
- Streamlit (interface)
- GeoPandas (géospatial)
- Folium (cartographie)
- Plotly (visualisation)
- Pandas (data)
- Requests (API)

** Installation
1. Cloner le projet
Shellgit clone https://github.com/ton-repo/projet-maroc.gitcd 
2. Installer les dépendances
Shellpython : -m pip install -r requirements.txtAfficher plus de lignes
3. Lancer l’application
Shellstreamlit : run app.py

Application déployée : https://ton-app.streamlit.app

Structure du projet
app/
│
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── Regions_WGS84.shp
│   ├── Provinces_WGS84.shp
│   └── communes_WGS84.shp

BINOME : EL MOUNIR BASMA 
         BAAIM FATIHA 
