from os import (
    path,
    makedirs,
)

from requests import (
    get,
)

from bs4 import (
    BeautifulSoup,
)

##################################################################################################################
# Cette classe permet de télécharger des images depuis une URL spécifiée et de les stocker dans des dossiers.
class ImageDownloader:
    # Initialisation de la classe avec l'URL de l'image et le dossier de l'image.
    def __init__(self, url_image, folder_image):
        self.url_image = url_image
        self.folder_image = folder_image
        self.maxj_folder = path.join(folder_image, "maxj")
        self.moyj_folder = path.join(folder_image, "moyj")
        self.polluants = ["NO2", "O3", "PM10", "PM25"]

    # Crée des dossiers pour chaque polluant dans les dossiers maxj et moyj.
    def create_polluant_folders(self):
        for folder in [self.maxj_folder, self.moyj_folder]:
            for polluant in self.polluants:
                makedirs(path.join(folder, polluant), exist_ok=True)

    # Télécharge les images de l'URL spécifiée et les stocke dans les dossiers correspondants.
    def download_images(self):
        response = get(self.url_image)
        soup = BeautifulSoup(response.content, "html.parser")
        file_links = [link.get("href") for link in soup.find_all("a") if link.get("href").endswith(".jpg")]

        for file_link in file_links:
            # Ignore les fichiers contenant le mot 'prevision'.
            if 'prevision' in file_link.lower():
                continue
            download_url = "http://www.prevair.org/donneesmisadispo/public/" + file_link
            filename = path.basename(download_url)  
            # Détermine le dossier de destination en fonction du nom du fichier.
            if "MAXJ" in filename:
                dest_folder = self.maxj_folder
            elif "MOYJ" in filename:
                dest_folder = self.moyj_folder
            else:
                continue

            # Vérifie si le fichier correspond à l'un des polluants et le stocke dans le bon dossier.
            for polluant in self.polluants:
                if polluant in filename:
                    polluant_folder = path.join(dest_folder, polluant)
                    break
            else:
                continue

            dest_path = path.join(polluant_folder, filename)

            # Si le fichier existe déjà, il n'est pas téléchargé à nouveau.
            if path.isfile(dest_path):
                print(f"Le fichier {filename} a déjà été téléchargé.")
                continue

            # Télécharge le fichier et l'enregistre dans le dossier de destination.
            response = get(download_url)
            with open(dest_path, "wb") as f:
                f.write(response.content)
                print(f"Le fichier {filename} a été téléchargé avec succès.")
##################################################################################################################