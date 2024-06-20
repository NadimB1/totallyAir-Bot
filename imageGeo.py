import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from PIL import Image
from pyproj import CRS
import rasterio
from rasterio import open as rasterio_open
from rasterio.plot import show, reshape_as_image
from rasterio.mask import mask
from rasterio.features import geometry_mask
from shapely.geometry import Polygon, shape





class ImageAnalysis:
    def __init__(self, image_path, geojson_path, output_path, tiff_path):
        self.image_path = image_path
        self.geojson_path = geojson_path
        self.output_path = output_path
        self.tiff_path = tiff_path

    # Cette fonction effectue l'analyse de l'image
    def runImage(self):
        # Ouvrir l'image
        
        img = Image.open(self.image_path)
        
        # Afficher l'image
        plt.imshow(img)
        plt.axis('off')
        print('image:')
        plt.show()

        # Définir la boîte de découpage pour la culture
        left = 33
        top = 119
        right = 1707
        bottom = 1880

        # Rogner l'image
        img_cropped = img.crop((left, top, right, bottom))

        # Afficher l'image rognée
        plt.imshow(img_cropped)
        plt.axis('off')
        print('image découpée:')
        plt.show()

        # Enregistrer l'image rognée
        img_cropped.save(self.output_path)

        # Charger le GeoJSON en tant que GeoDataFrame
        gdf = gpd.read_file(self.geojson_path)

        # Obtenir les limites géographiques (boîte englobante)
        bounds = gdf.total_bounds

        # Créer le graphique
        fig, ax = plt.subplots()

        # Tracer les entités géographiques sur l'axe du graphique
        gdf.plot(ax=ax)

        # Définir les limites de l'axe du graphique en utilisant les limites géographiques
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])

        # Activer la grille avec une transparence de 0.3
        ax.grid(True, alpha=0.3)

        # Afficher le graphique
        print('representation de notre Geojson:')
        plt.show()

        # Ouvrir l'image rognée
        img = Image.open(self.output_path)

        # Transformer l'image en un tableau numpy pour une manipulation facile
        img_array = np.array(img)

        # Obtenir les limites du GeoJSON
        bounds = gdf.total_bounds

        # Créer une figure et des axes
        fig, ax = plt.subplots()

        # Afficher l'image en arrière-plan avec l'étendue correspondant aux limites du GeoJSON
        ax.imshow(img_array, extent=[bounds[0], bounds[2], bounds[1], bounds[3]])

        # Tracer le GeoJSON par-dessus l'image
        gdf.plot(ax=ax, facecolor='none', edgecolor='red')

        # Définir les limites des axes
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])

        # Activer la grille
        ax.grid(True, alpha=0.3)

        # Afficher le graphique
        print("superposition du géojson sur l'image:" )
        plt.show()

        # Définir les coordonnées de la bbox
        bbox = {
            "type": "Polygon",
            "coordinates": [
                [
                    [-5.25, 41.35],
                    [9.66, 41.35],
                    [9.66, 51.12],
                    [-5.25, 51.12],
                    [-5.25, 41.35]
                ]
            ]
        }

        # Créer un objet de géométrie Polygon à partir des coordonnées de la bbox
        polygon = Polygon(bbox["coordinates"][0])

        # Définir la projection spatiale (CRS) de la bbox (WGS84)
        crs = CRS.from_epsg(4326)

        # Ouvrir le fichier JPEG avec Matplotlib pour visualiser l'image
        image = plt.imread(self.output_path)

        # Convertir l'image en niveaux de gris
        gray_image = image.mean(axis=2)

        # Créer le profil (métadonnées) pour le nouveau fichier TIFF géoréférencé
        profile = {
            'driver': 'GTiff',
            'dtype': rasterio.float32,
            'width': gray_image.shape[1],
            'height': gray_image.shape[0],
            'count': 1,  # Un seul canal (niveaux de gris)
            'crs': crs,
            'transform': rasterio.transform.from_bounds(*polygon.bounds, width=gray_image.shape[1], height=gray_image.shape[0]),
        }

        # Créer un masque booléen basé sur la bbox
        geom_mask = geometry_mask([polygon], out_shape=(gray_image.shape[0], gray_image.shape[1]), transform=profile['transform'], invert=True)

        # Appliquer le masque à l'image en niveaux de gris
        masked_image = gray_image * geom_mask.astype(rasterio.float32)

        # Enregistrer le nouveau fichier TIFF géoréférencé
        with rasterio_open(self.tiff_path, 'w', **profile) as dst:
            dst.write(masked_image, 1)  # Écrire l'image dans le canal 1
        print('superposition du géoreferancement')

        # Afficher l'image résultante avec la bbox
        with rasterio_open(self.tiff_path) as new_src:
            show(new_src)

        # Ouvrez le fichier TIFF en mode lecture
        with rasterio_open(self.tiff_path, "r+") as ds:
            # Affiche les informations de géoréférencement
            print("Système de référence de coordonnées (CRS) :", ds.crs)
            print("Transformation affine :\n", ds.transform)

        # Ouvrir le fichier TIFF en mode lecture
        with rasterio_open(self.tiff_path, "r+") as ds:
            # Convertir les coordonnées du pixel (500, 500) en coordonnées géographiques
            lon, lat = ds.xy(700, 500)

        # Afficher les coordonnées géographiques
        print("Coordonnées géographiques du pixel (500, 500) :", lon, lat)

        # Open the TIFF file in read mode
        with rasterio.open(self.tiff_path) as ds:
            # Load all departments from the GeoJSON file
            ile_de_france_codes = ['75', '77', '78', '91', '92', '93', '94', '95']

            # Load the GeoJSON file as a GeoDataFrame
            departments = gpd.read_file(self.geojson_path)
            ile_de_france = departments[departments['code'].isin(ile_de_france_codes)]

            # Display the image with the polygons using geopandas and rasterio
            fig, ax = plt.subplots()
            show(ds, ax=ax)
            ile_de_france.plot(ax=ax, facecolor='none', edgecolor='red')

            plt.show()

        # Define the department codes for Île-de-France
        ile_de_france_codes = ['75', '77', '78', '91', '92', '93', '94', '95']

        # Load all departments from the GeoJSON file
        departments = gpd.read_file(self.geojson_path)

        # Filter the departments to keep only those of Île-de-France
        ile_de_france = departments[departments['code'].isin(ile_de_france_codes)]

        # Prepare an empty DataFrame to store the results
        results = pd.DataFrame()
        print(results)

        from rasterio.mask import mask

        # Open the TIFF file
        with rasterio.open(self.tiff_path) as src:
            # Create a mask using the geometry of Île-de-France
            out_image, out_transform = mask(src, ile_de_france.geometry, crop=True)
            out_meta = src.meta.copy()

        # Update the metadata of the new image
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

        # Write the masked image to a new TIFF file
        with rasterio.open(r"C:\Users\nadim\Desktop\ttair\data\image\data\ile_de_france", "w", **out_meta) as dest:
            dest.write(out_image)

        # Open the new TIFF file and display the image
        with rasterio.open(r"C:\Users\nadim\Desktop\ttair\data\image\data\ile_de_france") as src:
            # Create a plot
            fig, ax = plt.subplots()

            # Display the image
            show(src, ax=ax)
            
            # Plot the boundaries of the departments of Île-de-France
            for idx, department in ile_de_france.iterrows():
                gpd.GeoSeries(department.geometry.boundary).plot(ax=ax, color='violet')
            
            # Remove the ticks from the x and y axes
            ax.set_xticks([])
            ax.set_yticks([])

            plt.show()
