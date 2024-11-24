
from pathlib import Path
import sys
# Add parent directory to path
parent_folder = Path(__file__).parent.parent
sys.path.append(str(parent_folder))

import os
from dotenv import load_dotenv
# import json
# import numpy as np
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
# from tqdm import tqdm
import time
from datetime import datetime
import shutil
# import glob

from mlops_msr.custom_logger import logger
from src.common_utils import load_txt, move_file_to_archives

# Load environment variables
load_dotenv()
# SIZE = int(os.getenv("SIZE", "20"))
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# API Limits and directories
REQUEST_LIMIT = 1
REQUEST_SLEEP = 35  # seconds between requests
DATA_DIR = Path("data")
URIS_DIR = DATA_DIR / "uris"
INTERIM_DIR = DATA_DIR / "interim"
URIS_DIR.mkdir(parents=True, exist_ok=True)
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Spotipy client
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)


# Function to fetch uris songs of a music genre
def get_genre_uris(music_genre: str, n_songs: int = 10, n_requests: int = REQUEST_LIMIT, sleep_time: int = REQUEST_SLEEP) -> pd.DataFrame:
    """
    Fetches song URIs from Spotify based on a given music genre.

    Args:
        music_genre (str): The music genre to query.
        n_songs (int, optional): Number of songs per API call. Defaults to 50.
        n_requests (int, optional): Number of API requests. Defaults to 2.
        sleep_time (int, optional): Time to sleep between API calls in seconds. Defaults to REQUEST_SLEEP.

    Returns:
        pd.DataFrame: DataFrame containing song URIs and genre.
    """
    uris_list = []
    for i in range(n_requests):
        try:
            print(f"Fetching {music_genre} - Request {i+1}/{n_requests}")
            logger.info(f"Fetching {music_genre} - Request {i+1}/{n_requests}")
            recs = sp.recommendations(seed_genres=[music_genre], limit=n_songs)
            uris_list.extend([track['uri'] for track in recs['tracks']])
            time.sleep(sleep_time)
        except Exception as e:
            print(f"Error fetching URIs for {music_genre} on request {i+1}: {e}")
            logger.info(f"Error fetching URIs for {music_genre} on request {i+1}: {e}")

    # Remove duplicates
    uris_list = list(set(uris_list))
    df = pd.DataFrame({"uri": uris_list, "genre": music_genre})

    # Save DataFrame to CSV
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # file_path = URIS_DIR / f"uris_{music_genre}_{timestamp}.csv"
    # df.to_csv(file_path, index=False)
    return df


# fetch audio features of a given songs uris
def get_audio_features(df_uris: pd.DataFrame) -> pd.DataFrame:
    
    num_batches = (len(df_uris) - 1) // 50 + 1
    df_features = pd.DataFrame()

    for i in range(num_batches):
        uri_batch = df_uris["uri"].iloc[i*50:(i+1)*50]
        try:
            features = sp.audio_features(uri_batch)
            df_features = pd.concat([df_features, pd.DataFrame(features)])
            time.sleep(REQUEST_SLEEP)  # Respect API rate limits
        except Exception as e:
            print(f"Error retrieving audio features for batch {i}: {e}")
            logger.info(f"Error retrieving audio features for batch {i}: {e}")

    df_audio = df_uris.merge(df_features, left_on="uri", right_on="uri", how="left")

    columns = ["uri", "genre", 'key', 'acousticness', 'danceability', 'energy',
               'instrumentalness', 'loudness', 'speechiness', 'valence', 'tempo']
    df_audio = df_audio[columns]
    df_audio["uri"] = df_audio["uri"].apply(lambda x: x.split(":")[-1])
    logger.info(f"Short view of df_audio:\n {df_audio.head(2)}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = INTERIM_DIR / f"songs_features_{timestamp}.csv"
    df_audio.to_csv(file_path, index=False)



# fonction to get audio features of songs for a specific music genre
def get_genre_songs_features(music_genre: str, n_songs: int = 10, n_requests: int = REQUEST_LIMIT, sleep_time: int = REQUEST_SLEEP):
    
    # fetch songs uris for music_genre
    df_uris = get_genre_uris(music_genre, n_songs, n_requests, sleep_time)

    # fecth audio features
    get_audio_features(df_uris)


# fonction to get audio features for a list of music genres
def get_all_genres_features():

    logger.info("Starting get_all_genres_features")

    genres = load_txt(Path("data/to_rec/genres.txt"))
    for genre in genres:
        print(f"Starting collecting {genre} audio features")
        get_genre_songs_features(genre)
        time.sleep(REQUEST_SLEEP + 15)
    print("Audio features collected for all given music genres")
    logger.info("Audio features collected for all given music genres")


# process all the songs collected from spotify
def process_song_data():

    logger.info("Starting process_song_data")

    # Définir le chemin du répertoire
    directory = "data/interim"
    
    # Vérifier si un fichier commençant par 'songs_df' existe
    files = [f for f in os.listdir(directory) if f.startswith('songs_df') and f.endswith('.csv')]
    
    # Étape 1 et 2 : Charger le fichier dans un DataFrame song_df_0 s'il existe
    if files:
        files.sort(reverse=True)
        file_path = os.path.join(directory, files[0])
        print(file_path)
        song_df_0 = pd.read_csv(file_path, index_col=0)
        move_file_to_archives(file_path)
    else:
        song_df_0 = pd.DataFrame({})  # Si aucun fichier n'est trouvé, créer un DataFrame vide
    
    # Étape 4 : Charger et concaténer les fichiers commençant par 'songs_features'
    feature_files = [f for f in os.listdir(directory) if f.startswith('songs_features') and f.endswith('.csv')]
    for feature_file in feature_files:
        feature_path = os.path.join(directory, feature_file)
        feature_df = pd.read_csv(feature_path)
        song_df_0 = pd.concat([song_df_0, feature_df], axis=0, ignore_index=True)
        move_file_to_archives(feature_path)
    
    # Étape 5 : Sauvegarder le DataFrame avec un timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_path = os.path.join(directory, f"song_df_{timestamp}.csv")
    song_df_0.to_csv(output_file_path)
    
    print(f"DataFrame sauvegardé dans : {output_file_path}")


# process and merge song collected with the current songs database
def process_and_merge_song_data():
    
    logger.info("Starting process_and_merge_song_data")
    
    # 1 - Charger le fichier "data/raw/song_df.csv" dans df_old et compter le nombre de chansons
    df_old = pd.read_csv("data/raw/song_df.csv", index_col=0)
    n_songs = len(df_old)
    
    # 2 - Charger le fichier le plus ancien dans "data/interim" qui commence par "song_df"
    interim_directory = "data/interim"
    
    # Trouver tous les fichiers qui commencent par "song_df" et se terminent par ".csv"
    song_df_files = [f for f in os.listdir(interim_directory) if f.startswith("song_df") and f.endswith(".csv")]
    print("song_df_files:\n", song_df_files)
    
    # Si des fichiers sont trouvés, charger le plus récent (par date de création).
    if song_df_files:
        # Trier les fichiers par date de modification (les plus récents en premier).
        # song_df_files.sort(key=lambda x: os.path.getmtime(os.path.join(interim_directory, x)))
        song_df_files.sort(reverse=True)
        # Charger le fichier le plus récent.
        file_to_add = song_df_files[0]
        print(f"file_to_add: {file_to_add}")
        df_to_add = pd.read_csv(os.path.join(interim_directory, file_to_add), index_col=0)
        print("df_to_add:")
        print(df_to_add.info())
    else:
        raise FileNotFoundError("Aucun fichier song_df trouvé dans data/interim")
    
    # 3 - Concaténer df_old et df_to_add dans df_new, en supprimant les doublons sur la colonne "uri"
    df_new = pd.concat([df_old, df_to_add], axis=0, ignore_index=True)
    df_new = df_new.drop_duplicates(subset=["uri"], ignore_index=True)  # Supprimer les doublons en fonction de la colonne "uri"
    
    # 4 - Calculer n_songs_new et delta
    n_songs_new = len(df_new)
    delta = (n_songs_new - n_songs) / n_songs
    
    # 5 - Afficher les résultats
    print("n_songs_old:", n_songs)
    print("n_songs_new:", n_songs_new)
    print(f"delta: {delta * 100:.2f}%")  # Affichage du delta en pourcentage

    # 6 - Sauvegarde dans un ficher csv
    df_new.to_csv("data/new/song_df.csv")


# check if there a new songs in the songs collected from Spotify
def check_and_load_new_data():
    
    logger.info("Starting check_and_load_new_data")
    
    # Load the old and new data files, ensuring the index column is correctly set
    df_old = pd.read_csv("data/raw/song_df.csv", index_col=0)
    df_new = pd.read_csv("data/new/song_df.csv", index_col=0)
    logger.info(f"Current number of songs: {len(df_old)}")
    logger.info(f"New number of songs: {len(df_new)}")

    # Calculate the number of songs in each dataset
    n_songs_old = len(df_old)
    n_songs_new = len(df_new)

    # Calculate the percentage increase in song count
    delta = (n_songs_new - n_songs_old) / n_songs_old if n_songs_old > 0 else float('inf')
    logger.info(f"delta: {delta * 100: .2f}")

    # Save df_new to "data/raw/song_df.csv" if delta > 0 (indicating new songs)
    if delta > 0:
        
        logger.info("Delta > 0. New data to load into the pipeline")
        
        # Archive the old data file with a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"song_df_{timestamp}.csv"
        
        # Rename and move the old file to an archive folder
        shutil.move("data/raw/song_df.csv", f"data/raw/{archive_filename}")
        move_file_to_archives(f"data/raw/{archive_filename}")
        
        shutil.move("data/new/song_df.csv", f"data/new/{archive_filename}")
        move_file_to_archives(f"data/new/{archive_filename}")
        
        # Replace old data with new data in the Ingestion Step of the pipeline
        df_new.to_csv("data/raw/song_df.csv")
        print("New data loaded in the pipeline.")
        logger.info("New data loaded in the pipeline.")
        logger.info(f"New data info :\n {df_new.info()}")

        # Set the environment variable RETRAIN=1 to trigger retraining
        with open('data/raw/retrain.log', 'w') as f:
            f.write('RETRAIN=1')                
        print("logged RETRAIN=1 into data/raw/retrain.log file")
        logger.info("written RETRAIN=1 into data/raw/retrain.log file")
    else:
        print("No new songs to add.")
        logger.info("No new songs to add.")
        
if __name__ == "__main__":
    
    logger.info("Running data feeding")
    
    get_all_genres_features()
    process_song_data()
    process_and_merge_song_data()
    check_and_load_new_data()