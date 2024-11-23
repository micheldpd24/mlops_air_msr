
import os
import subprocess
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import time
from datetime import datetime, timedelta
import shutil
import glob

from custom_logger import logger

# -------
from pathlib import Path
# import sys
# # Add parent directory to path
# parent_folder = Path(__file__).parent.parent
# sys.path.append(str(parent_folder))

# --------

# Load environment variables
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

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


def load_txt(path: Path):
    """Loads data from a text file into a list.
    Args:
        file_path: The path to the text file containing the genres.
    Returns:
        A list of lines content of the txt file.
    """

    data = []
    with open(path, 'r') as f:
        for line in f:
            x = line.strip()
            if x:
                data.append(x)

    # logger.info(f"text file loaded succesfully from: {path}")
    print(f"text file loaded succesfully from: {path}")
    
    return data


# function to move file to .archives folder
def move_file_to_archives(file_path: str):
    """
    Moves a specified file to the .archives directory in its current location.
    """
    file = Path(file_path)
    archives_dir = file.parent / ".archives"
    archives_dir.mkdir(exist_ok=True)  # Create .archives if it doesn't exist
    shutil.move(str(file), archives_dir / file.name)


# function to navigate dags and mlops_msr directories
def navigate_between_folders(current_folder: str, target_folder: str):
    """
    Navigate from folder A to folder B, where both are subfolders of the same parent directory.
    
    :param current_folder: The current folder name (relative or absolute path).
    :param target_folder: The target folder name (relative to the parent directory).
    """
    # Get the absolute path of the current folder
    current_dir = os.path.abspath(current_folder)
    print(f"Current directory: {current_dir}")
    # logger.info(f"Current directory: {current_dir}")

    # Move up to the parent directory
    parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
    print(f"Parent directory: {parent_dir}")
    # logger.info(f"Parent directory: {parent_dir}")

    # Construct the path to the target folder
    target_dir = os.path.join(parent_dir, target_folder)
    if not os.path.isdir(target_dir):
        raise FileNotFoundError(f"Target directory '{target_dir}' does not exist.")

    # Change to the target folder
    os.chdir(target_dir)
    print(f"Now in directory: {os.getcwd()}")
    # logger.info(f"Now in directory: {os.getcwd()}")


# function to delete all file into a given directory
def delete_csv_files(directory):
    # Pattern to find all .csv files in the directory
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    
    # Delete each .csv file
    for file_path in csv_files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")


def delete_folder(folder_path):
    """
    Deletes the folder at the specified path. This will delete the folder and all of its contents.

    Args:
    folder_path (str): The path to the folder that should be deleted.
    """
    try:
        # Check if the folder exists before attempting to delete
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)  # Recursively delete the folder and its contents
            print(f"The folder {folder_path} has been deleted.")
        else:
            print(f"The folder {folder_path} does not exist or is not a valid directory.")
    except Exception as e:
        print(f"Error deleting the folder {folder_path}: {e}")


def get_most_recent_file(directory, prefix, extension=".csv"):
    """Finds and returns the most recent file in a directory that matches the prefix and extension."""
    song_df_files = [
        f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith(extension)
    ]
    if not song_df_files:
        raise FileNotFoundError(f"No files starting with '{prefix}' found in {directory}")
    
    song_df_files.sort(reverse=True)  # Sort by modification time (latest first)
    most_recent_file = song_df_files[0]
    print(f"Most recent file found: {most_recent_file}")
    # logger.info(f"Most recent file found: {most_recent_file}")
    return most_recent_file


def archive_old_file(file_path, archive_dir):
    """Archives a file by renaming and moving it to the archive directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_{timestamp}.csv"
    archive_path = os.path.join(archive_dir, archive_filename)
    shutil.move(file_path, archive_path)
    print(f"File archived: {archive_path}")
    # logger.info(f"File archived: {archive_path}")
    return archive_path


def log_retrain_signal():
    """Logs the RETRAIN signal by writing to a file."""
    with open('data/raw/retrain.log', 'w') as f:
        f.write('RETRAIN=1')
    print("Logged RETRAIN=1 into data/raw/retrain.log")
    # logger.info("Logged RETRAIN=1 into data/raw/retrain.log")


# Function to fetch uris songs of a music genre
def get_genre_uris(music_genre: str, n_songs: int = 5, n_requests: int = REQUEST_LIMIT, sleep_time: int = REQUEST_SLEEP) -> pd.DataFrame:
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
            # logger.info(f"Fetching {music_genre} - Request {i+1}/{n_requests}")
            recs = sp.recommendations(seed_genres=[music_genre], limit=n_songs)
            uris_list.extend([track['uri'] for track in recs['tracks']])
            time.sleep(sleep_time)
        except Exception as e:
            print(f"Error fetching URIs for {music_genre} on request {i+1}: {e}")
            # logger.info(f"Error fetching URIs for {music_genre} on request {i+1}: {e}")

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
            # logger.info(f"Error retrieving audio features for batch {i}: {e}")

    df_audio = df_uris.merge(df_features, left_on="uri", right_on="uri", how="left")

    columns = ["uri", "genre", 'key', 'acousticness', 'danceability', 'energy',
               'instrumentalness', 'loudness', 'speechiness', 'valence', 'tempo']
    df_audio = df_audio[columns]
    df_audio["uri"] = df_audio["uri"].apply(lambda x: x.split(":")[-1])
    print(f"Short view of df_audio:\n {df_audio.head(2)}")
    #logger.info(f"Short view of df_audio:\n {df_audio.head(2)}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = INTERIM_DIR / f"songs_features_{timestamp}.csv"
    df_audio.to_csv(file_path, index=False)


# fonction to get audio features of songs for a specific music genre
def get_genre_songs_features(music_genre: str, n_songs: int = 20, n_requests: int = REQUEST_LIMIT, sleep_time: int = REQUEST_SLEEP):
    
    # fetch songs uris for music_genre
    df_uris = get_genre_uris(music_genre, n_songs, n_requests, sleep_time)

    # fecth audio features
    get_audio_features(df_uris)


# fonction to get audio features for a list of music genres
def get_all_genres_features():

    # logger.info("Starting get_all_genres_features")
    print("Starting get_all_genres_features")

    genres = load_txt(Path("data/to_rec/genres.txt"))
    for genre in genres:
        print(f"Starting collecting {genre} audio features")
        get_genre_songs_features(genre)
        time.sleep(REQUEST_SLEEP + 15)
    print("Audio features collected for all given music genres")
    # logger.info("Audio features collected for all given music genres")


# process all the songs collected from spotify
def process_song_data():

    # logger.info("Starting process_song_data")
    print("Starting process_song_data")

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
    print(f"DataFrame saved into : {output_file_path}")


def run_python_stage(stage_file_path):
    try:
        print("==== stage01 data ingestion ====")
        result = subprocess.run(["python", DIR_STEPS / "stage01_data_ingestion.py"], check=True, capture_output=True, text=True)
        print("Command executed successfully!")
        print(result.stdout)  # Display standard output

    except subprocess.CalledProcessError as e:
        print("Error while executing command.")
        print(e.stderr)  # Display error output


def run_stage(stage_name, script_name):
    
    # Pipeline Directory
    DIR_STEPS = Path("mlops_msr/src/pipeline_steps")
    
    try:
        print(f"==== {stage_name} ====")
        result = subprocess.run(
            ["python", DIR_STEPS / script_name], 
            check=True, 
            capture_output=True, 
            text=True
        )
        print("Command executed successfully!")
        print(result.stdout)  # Display standard output

    except subprocess.CalledProcessError as e:
        print(f"Error while executing {stage_name}.")
        print(e.stderr)  # Display error output
