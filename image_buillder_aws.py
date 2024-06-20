import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from PIL import Image
from pyproj import CRS
from rasterio import open as rasterio_open
import rasterio
from rasterio.plot import show, reshape_as_image
from rasterio.mask import mask
from rasterio.features import geometry_mask
from shapely.geometry import Polygon, shape
import boto3
import io

# Initialize the Boto3 S3 client with your AWS credentials
s3_client = boto3.client(
    's3',
    aws_access_key_id='REMOVED_FOR_SECURITY_REASONS',
    aws_secret_access_key='REMOVED_FOR_SECURITY_REASONS'
)

# Specify the S3 bucket name and folder path
s3_bucket_name = 'air-quality-data-totallyair'
s3_folder_path = 'air_quality_images/MAXJ/PM25/'
s3_folder_send_user_side = 'Image_to_send_user/'
s3_image_name = 'cropped_paris'

# Function to retrieve the latest image from S3
def get_latest_image_from_s3(bucket_name, folder_path):
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)

    # Filter only the objects that are image files (assuming they have ".jpg" extension)
    image_files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.jpg')]

    # If there are no image files in the folder, exit the script or handle the case accordingly
    if not image_files:
        print("No image files found in the specified folder.")
        return None

    # Sort the image files based on the last modified time
    image_files.sort(key=lambda x: s3_client.head_object(Bucket=bucket_name, Key=x)['LastModified'], reverse=True)

    # Get the latest image file (the first one after sorting)
    latest_image_key = image_files[0]

    # Download the latest image to a local directory (optional)
    local_output_path = os.path.join('output', latest_image_key.split('/')[-1] + '_output.jpg')
    s3_client.download_file(bucket_name, latest_image_key, local_output_path)

    return local_output_path

# Get the latest image from the S3 folder
image_path_output = get_latest_image_from_s3(s3_bucket_name, s3_folder_path)
if not image_path_output:
    print("No image found. Exiting the script.")
    exit()

# Read the latest image using PIL
img = Image.open(image_path_output)

# Define the bounding box for the crop
left = 33
top = 119
right = 1707
bottom = 1880

# Crop the image
img_cropped = img.crop((left, top, right, bottom))

# Save the cropped image in the "output" folder
output_folder = 'output'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
cropped_image_path = os.path.join(output_folder, 'cropped_image.jpg')
img_cropped.save(cropped_image_path)

# Charger le GeoJSON en tant que GeoDataFrame
geojson_path = r"test.geojson"
gdf = gpd.read_file(geojson_path)

# Get the bounding box of the GeoJSON
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

# Save the plot in the "output" folder
overlay_plot_path = os.path.join(output_folder, 'overlay_plot.jpg')
plt.savefig(overlay_plot_path, format='jpg')

gdf = gpd.read_file(geojson_path)

# Lire l'image
img = Image.open(image_path_output)

# Transformer l'image en un tableau numpy pour une manipulation facile
img_array = np.array(img)

# Créer une figure et des axes
fig, ax = plt.subplots()

# Afficher l'image en arrière-plan avec l'étendue correspondant aux limites du GeoJSON
ax.imshow(img_array, extent=[bounds[0], bounds[2], bounds[1], bounds[3]])

# Tracer le GeoJSON par dessus l'image
gdf.plot(ax=ax, facecolor='none', edgecolor='red')

# Définir les limites des axes
ax.set_xlim(bounds[0], bounds[2])
ax.set_ylim(bounds[1], bounds[3])

# Activer la grille
ax.grid(True, alpha=0.3)

# Afficher le graphique
print("superposition du géojson sur l'image:")

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

# Convertir l'image en niveaux de gris
gray_image = np.array(img.convert('L'))

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
mask = geometry_mask([polygon], out_shape=(gray_image.shape[0], gray_image.shape[1]), transform=profile['transform'], invert=True)

# Appliquer le masque à l'image en niveaux de gris
masked_image = gray_image * mask.astype(rasterio.float32)

# Enregistrer le nouveau fichier TIFF géoréférencé
output_tiff_path = os.path.join(output_folder, 'image.tif')
with rasterio.open(output_tiff_path, 'w', **profile) as dst:
    dst.write(masked_image, 1)  # Écrire l'image dans le canal 1

# Ouvrez le fichier TIFF en mode lecture
with rasterio.open(output_tiff_path, "r+") as ds:
    # Affiche les informations de géoréférencement
    print("Système de référence de coordonnées (CRS) :", ds.crs)
    print("Transformation affine :\n", ds.transform)
    
# Ouvrir le fichier TIFF en mode lecture
with rasterio.open(output_tiff_path, "r+") as ds:
    # Convertir les coordonnées du pixel (500, 500) en coordonnées géographiques
    lon, lat = ds.xy(700, 500)

# Afficher les coordonnées géographiques
print("Coordonnées géographiques du pixel (500, 500) :", lon, lat)

# Open the TIFF file in read mode
with rasterio.open(output_tiff_path) as ds:
    # Load all departments from the GeoJSON file
    ile_de_france_codes = ['75', '77', '78', '91', '92', '93', '94', '95']

# Load the GeoJSON file as a GeoDataFrame
    departments = gpd.read_file(geojson_path)
    ile_de_france = departments[departments['code'].isin(ile_de_france_codes)]

    # Display the image with the polygons using geopandas and rasterio
    fig, ax = plt.subplots()
    show(ds, ax=ax)
    ile_de_france.plot(ax=ax, facecolor='none', edgecolor='red')

    #plt.show()
    
    # Create a plot


# Define the department codes for Île-de-France
ile_de_france_codes = ['75', '77', '78', '91', '92', '93', '94', '95']

# Load all departments from the GeoJSON file
departments = gpd.read_file(geojson_path)

# Filter the departments to keep only those of Île-de-France
ile_de_france = departments[departments['code'].isin(ile_de_france_codes)]

# Prepare an empty DataFrame to store the results
results = pd.DataFrame()
print(results)

from rasterio.mask import mask

# Open the TIFF file
with rasterio.open(output_tiff_path) as src:
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
with rasterio.open('ile_de_france.tif', "w", **out_meta) as dest:
    dest.write(out_image)

# Open the new TIFF file and display the image
with rasterio.open('ile_de_france.tif') as src:
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
    plt.savefig('image_to_use.jpg', format='jpg')

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='jpg')
    image_stream.seek(0)  # rewind the file pointer to the beginning of the stream
    
    
    s3_client.upload_fileobj(image_stream, s3_bucket_name, 'Image_to_send_user/image_to_use.jpg')
    # Upload the image to the S3 bucket
    #s3_client.meta.client.upload_file('image_to_use.jpg', s3_bucket_name, s3_folder_send_user_side + s3_image_name)
