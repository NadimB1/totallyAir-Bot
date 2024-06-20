from PIL import Image

from sklearn.model_selection import (
    train_test_split,
)

from tensorflow.keras.models import (
    Sequential,
)

from tensorflow.keras.layers import (
    Conv2D,
    Conv2DTranspose,
    BatchNormalization,
)

import os
import matplotlib.pyplot as plt
import cv2
import numpy as np

##################################################################################################################
class ImageProcessor:
    def __init__(self, base_dir, parent_dir, output_dir, sub_dirs, coordinates):
        # Initialiser les variables de classe
        self.base_dir = base_dir
        self.parent_dir = parent_dir
        self.output_dir = output_dir
        self.sub_dirs = sub_dirs
        self.coordinates = coordinates
        # Créer la liste des répertoires d'images
        self.image_dirs = [os.path.join(self.parent_dir, sub_dir) for sub_dir in self.sub_dirs]
        # Créer le répertoire de sortie s'il n'existe pas déjà
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_subdirectories(self):
        # Parcourir chaque sous-répertoire
        for sub_dir in self.image_dirs:
            # Parcourir chaque fichier du sous-répertoire
            for filename in os.listdir(sub_dir):
                # Vérifier si le fichier est une image JPEG et n'est pas une image de sortie
                if filename.endswith(".jpg") and "output.jpg" not in filename:
                    # Créer les chemins du fichier d'entrée et de sortie
                    input_file_path = os.path.join(sub_dir, filename)
                    output_file_path = os.path.join(sub_dir, filename.replace(".jpg", "_output.jpg"))
                    
                    # Vérifier si le fichier de sortie existe déjà
                    if os.path.exists(output_file_path):
                        print(f"Output file {output_file_path} already exists. Skipping processing for {input_file_path}.")
                        continue

                    try:
                        # Ouvrir l'image, la recadrer et sauvegarder l'image de sortie
                        img = Image.open(input_file_path)
                        img_cropped = img.crop(self.coordinates)
                        img_cropped.save(output_file_path)

                    except Exception as e:
                        # Afficher une erreur si une exception est levée lors du traitement de l'image
                        print(f"Error processing file {input_file_path}: {str(e)}")

            print(f"Finished processing {sub_dir}\n")

    def load_images_with_output(self, image_dir):
        # Charger les images de sortie du répertoire d'images spécifié
        image_files = os.listdir(image_dir)
        image_files = sorted(image_files)  
        images = []
        for image_file in image_files:
            # Charger uniquement les images de sortie
            if "_output.jpg" in image_file:
                # Charger l'image, la redimensionner et l'ajouter à la liste des images
                image = cv2.imread(os.path.join(image_dir, image_file))
                image = cv2.resize(image, (256, 256))
                images.append(image)
        # Convertir la liste des images en un tableau numpy et normaliser les valeurs des pixels
        images = np.array(images) / 255.0
        return images, os.path.basename(image_dir)

    def train_and_save(self):
        # Entraîner le modèle et sauvegarder les résultats
        for image_dir in self.image_dirs:
            # Charger les images de sortie
            images, gas_type = self.load_images_with_output(image_dir)
            # Créer les ensembles de données d'entraînement et de test
            X = images[:-1]  
            y = images[1:] 
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.7, random_state=42)
            # Créer le modèle de réseau neuronal convolutif
            generator = Sequential([
                Conv2D(64, kernel_size=(3, 3), strides=(2, 2), padding="same", activation="relu", input_shape=(256, 256, 3)),
                BatchNormalization(),
                Conv2D(128, kernel_size=(3, 3), strides=(2, 2), padding="same", activation="relu"),
                BatchNormalization(),
                Conv2DTranspose(64, kernel_size=(3, 3), strides=(2, 2), padding="same", activation="relu"),
                BatchNormalization(),
                Conv2DTranspose(3, kernel_size=(3, 3), strides=(2, 2), padding="same", activation="sigmoid"),
            ])
            # Compiler le modèle
            generator.compile(optimizer="adam", loss="mean_squared_error")
            # Entraîner le modèle
            generator.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=5)
            # Prédire les images à partir des données de test
            predicted_images = generator.predict(X_test)
            # Sauvegarder l'image prédite
            output_file = os.path.join(self.output_dir, f"predicted_{gas_type}_output.png")
            plt.imshow(predicted_images[0])
            plt.savefig(output_file)
            # Afficher les résultats
            self.display_results(X_test, predicted_images)
        
    def display_results(self, X_test, predicted_images):
        # Afficher l'image originale et l'image prédite côte à côte
        plt.figure(figsize=(10, 5))
        plt.subplot(1, 2, 1)
        plt.title("Original Image")
        plt.imshow(X_test[0])
        plt.subplot(1, 2, 2)
        plt.title("Predicted Image")
        plt.imshow(predicted_images[0])
        plt.show()
