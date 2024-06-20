import os
import pandas as pd
import numpy as np
from collections import defaultdict

from os import (
    listdir,
    path,
)

from bs4 import BeautifulSoup
from pandas import (
    DataFrame,
    concat,
    read_csv,
)

from requests import (
    get,
)

##################################################################################################################
class GazsData:
    # Initialisation de la classe avec le dossier de téléchargement des fichiers CSV.
    def __init__(self, download_folder):
        self.download_folder = download_folder
        self.url = "https://files.data.gouv.fr/lcsqa/concentrations-de-polluants-atmospheriques-reglementes/temps-reel/"

    # Télécharge les fichiers CSV depuis une URL donnée.
    def download_csv_files(self, target_year="2021"):
        downloaded_files = listdir(self.download_folder)
        response = get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Parcoure les dossiers de chaque année sur la page web.
        for year_folder in soup.select('a[href$="/"]'):
            year = year_folder['href'].strip('/')
            if year == target_year:
                year_url = self.url + year_folder['href']
                response_year = get(year_url)
                soup_year = BeautifulSoup(response_year.text, 'html.parser')

                # Parcoure les fichiers CSV dans chaque dossier annuel.
                for csv_file in soup_year.select('a[href$=".csv"]'):
                    csv_url = year_url + csv_file['href']
                    csv_filename = path.join(self.download_folder, csv_file['href'])

                    # Si le fichier CSV n'a pas encore été téléchargé, le télécharge.
                    if csv_file['href'] not in downloaded_files:
                        with open(csv_filename, 'wb') as f:
                            f.write(get(csv_url).content)

                            print(f"Le fichier {csv_file['href']} a été téléchargé avec succès.")

                    downloaded_files.append(csv_file['href'])

    # Lit un fichier CSV spécifique et renvoie un DataFrame pandas.
    def read_csv(self, f):
        file_path = path.join(self.download_folder, f)

        if path.getsize(file_path) > 0:  # Vérifie si le fichier n'est pas vide
            df = read_csv(file_path, sep=';')
            return df
        else:
            print(f'Le fichier {f} est vide et ne peut pas être lu.')
            return DataFrame()  # Retourne un DataFrame vide

class GazDataProcessor:
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder

    # Définit une fonction d'agrégation personnalisée pour utiliser dans la méthode groupby
    def custom_agg(self, x):
        if pd.api.types.is_string_dtype(x):
            return x.iloc[0]
        elif pd.api.types.is_numeric_dtype(x):
            return x.mean()
        else:
            return np.nan

    # Traite les fichiers CSV pour nettoyer les données et extraire les informations pertinentes
    def process_csv_files(self):
        # Parcourir tous les fichiers du répertoire
        for file_name in os.listdir(self.input_folder):
            # Vérifier si le fichier est un fichier CSV et ne se termine pas par '_output.csv'
            if file_name.endswith('.csv') and not file_name.endswith('_output.csv'):
                # Définir le chemin complet du fichier
                file_path = os.path.join(self.input_folder, file_name)

                # Vérifier si le fichier de sortie existe déjà
                output_file_name = file_name[:-4] + '_output.csv'
                output_file_path = os.path.join(self.output_folder, output_file_name)
                if os.path.exists(output_file_path):
                    print(f"Output file {output_file_name} already exists in the output folder. Skipping this file.")
                    continue

                # Charger les données
                data = pd.read_csv(file_path, sep=';')

                # Vérifier si les colonnes 'Polluant' et 'Zas' existent dans le DataFrame
                if 'Polluant' not in data.columns or 'Zas' not in data.columns:
                    print(f"'Polluant' or 'Zas' column not found in {file_name}. Skipping this file.")
                    continue

                # Remplacer les polluants selon les conditions données
                data['Polluant'] = data['Polluant'].replace({'NO': 'NO2', 'NOX': 'NO2', 'NOX as NO2': 'NO2', 'PM2.5': 'PM25'})

                # Supprimer les lignes contenant 'C6H6', 'SO2', et 'CO' dans la colonne 'Polluant'
                data = data[~data['Polluant'].isin(['C6H6', 'SO2', 'CO'])]

                # Définir les colonnes d'intérêt
                cols_of_interest = ['Date de début', 'Date de fin', 'Polluant', 'valeur', 'code qualité', 'unité de mesure']

                # Supprimer les lignes contenant des valeurs vides dans les colonnes d'intérêt
                data = data.dropna(subset=cols_of_interest)

                # Convertir 'Date de fin' au format datetime et extraire uniquement la date
                data['Date de fin'] = pd.to_datetime(data['Date de fin']).dt.date

                # Grouper par 'Date de fin', 'Polluant', et 'Zas' et calculer la moyenne de 'valeur'
                # Garder aussi les autres colonnes en prenant la première valeur de chaque groupe
                grouped_data = data.groupby(['Date de fin', 'Polluant', 'Zas']).agg(self.custom_agg).reset_index()

                # Supprimer les colonnes spécifiées
                grouped_data = grouped_data.drop(columns=['taux de saisie', 'couverture temporelle', 'couverture de données'])
                grouped_data['unité de mesure'] = grouped_data['unité de mesure'].str.replace('Â', '')

                # Sélectionner les colonnes à conserver selon l'analyse
                cols_to_keep = ['Date de fin', 'Polluant', 'Zas', "type d'implantation", "type d'influence", "type d'évaluation", 'procédure de mesure', 'valeur', 'code qualité', 'unité de mesure']

                # Créer un nouveau DataFrame contenant uniquement les colonnes à conserver
                final_data = grouped_data[cols_to_keep]

                # Sauvegarder le DataFrame final dans un nouveau fichier CSV
                final_data.to_csv(output_file_path, index=False)
