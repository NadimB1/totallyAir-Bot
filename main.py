# Import des classes nécessaires.
import os
from imageProcessor import ImageProcessor
from imageDownloader import ImageDownloader
from pollensData import PollensDataManager
from gazsData import GazsData, GazDataProcessor
from imageGeo import ImageAnalysis

# Téléchargement des images de polluants
url_image = "http://www.prevair.org/donneesmisadispo/public/?C=N;O=A"
folder_image = r"C:/Users/nadim/Desktop/ttair/data/image"

image_downloader = ImageDownloader(url_image, folder_image)
image_downloader.create_polluant_folders()  # Crée les dossiers nécessaires pour chaque polluant.
image_downloader.download_images()  # Télécharge les images.

# Traitement des images téléchargées
base_dir = r"C:/Users/nadim/Desktop/ttair/data/image"
parent_dir = os.path.join(base_dir, 'maxj')
output_dir = os.path.join(base_dir, 'prediction')
sub_dirs = ["NO2", "O3", "PM25", "PM10"]

coordinates = [119, 33, 1707, 1880]  # Coordinates for cropping, adjust as needed
image_processor = ImageProcessor(base_dir, parent_dir, output_dir, sub_dirs, coordinates)
image_processor.process_subdirectories()
image_processor.train_and_save()

# Téléchargement et sauvegarde des données sur les pollens
url_pollens = "https://api.airparif.fr/pollens/bulletin"
folder_path = r"C:\Users\nadim\Desktop\ttair\data\pollens"
pollens_data_manager = PollensDataManager(url_pollens, folder_path)
pollens_data_manager.save_pollens_data_to_csv()  # Sauvegarde les données de pollens dans un fichier CSV.

# Téléchargement et fusion des données sur les gaz
# Téléchargement et fusion des données sur les gaz
download_folder = r'C:\Users\nadim\Desktop\ttair\data\gazs'
gazs_data = GazsData(download_folder)
gazs_data.download_csv_files()  # Télécharge les fichiers CSV contenant les données sur les gaz.

# Traitement des données sur les gaz
input_folder = r"C:\Users\nadim\Desktop\ttair\data\gazs"
output_folder = r"C:\Users\nadim\Desktop\ttair\data\gazs_output"

gaz_data_processor = GazDataProcessor(input_folder, output_folder)
gaz_data_processor.process_csv_files()

image_path = r"C:\Users\nadim\Desktop\ttair\data\image\moyj\NO2\PREVAIR.analyse.20230614.MOYJ.NO2.public.jpg"
output_path = r"C:\Users\nadim\Desktop\ttair\data\image\prediction\no2_output.png"
geojson_path = r"C:\Users\nadim\Desktop\ttair\data\image\data\test.geojson"
tiff_path = r'C:\Users\nadim\Desktop\ttair\data\image\prediction\image.tif'
analysis = ImageAnalysis(image_path, geojson_path, output_path, tiff_path)
analysis.runImage()