# les bibliothèques nécessaires 
import datetime

from os import (
    path,
)

from pandas import (
    DataFrame, 
    Timestamp,
)

from requests import (
    get,
)

##################################################################################################################
# Cette classe récupère les données sur les pollens à partir d'une URL donnée
class PollensData:
    # Le constructeur initialise l'URL et les en-têtes de la requête
    def __init__(self, url_pollens):
        self.url_pollens = url_pollens
        self.headers = {"X-Api-Key": "YOUR API KEY"}

    # Cette méthode effectue la requête HTTP et transforme la réponse en DataFrame pandas
    def get_pollens_data(self):
        res = get(self.url_pollens, headers=self.headers)
        data_air_parif = res.json()
        data = data_air_parif['data']
        columns = []
        pollen_names = data[0]['taxons']

        # On itère sur chaque observation pour créer les colonnes du DataFrame
        for observation in data:
            values = observation['valeurs']

            for departement, pollen_counts in values.items():
                row = {'departement': departement}

                for i, count in enumerate(pollen_counts):
                    pollen_name = pollen_names[i]
                    row[pollen_name] = count

                columns.append(row)

        # On crée le DataFrame
        df_pollens = DataFrame(columns)
        df_pollens['departement'] = df_pollens['departement'].astype(int)
        df_pollens['time'] = Timestamp.today().date()

        return df_pollens

# Cette classe gère le stockage des données des pollens
class PollensDataManager:
    # Le constructeur initialise la source des données et le chemin du dossier de stockage
    def __init__(self, url_pollens, folder_path):
        self.pollens_data = PollensData(url_pollens)
        self.folder_path = folder_path

    # Cette méthode enregistre les données des pollens dans un fichier CSV
    def save_pollens_data_to_csv(self):
        df_pollens = self.pollens_data.get_pollens_data()
        filename = f"csv_pollen_{datetime.date.today().strftime('%d-%m-%Y')}.csv"
        filepath = path.join(self.folder_path, filename)

        # Si le fichier existe déjà, on affiche un message
        if path.exists(filepath):
            print(f"Le fichier {filename} existe déjà.")
        # Sinon, on enregistre le DataFrame dans un fichier CSV et on affiche un message de confirmation
        else:
            df_pollens.to_csv(filepath, index=False)
            print(f"Le DataFrame a été enregistré sous le nom de fichier : {filepath}")
            print(df_pollens)
##################################################################################################################