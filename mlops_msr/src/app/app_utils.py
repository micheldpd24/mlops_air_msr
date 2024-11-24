
import sys
from pathlib import Path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm

from dotenv import load_dotenv
import time
import re
import pandas as pd
import numpy as np
import json

from datetime import datetime

from src.pipeline_steps.prediction import PredictionPipeline, RecommendationPipeline
from src.common_utils import load_txt, save_json

# Load environment variables
load_dotenv()


# keys to connect to Spotify API
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# Call an instance of Spotipy API
auth_manager = SpotifyClientCredentials(
    client_id=client_id,  # to replace by your CID key
    client_secret=client_secret  # to replace by your SECRET key
  )
sp = spotipy.Spotify(auth_manager=auth_manager)

# Size of extract of playlists from million playlist dataset
SIZE = os.getenv("SIZE")

# playlists summaries of playlists from extract from million playlists dataset
JSON_FILE_PATH = "data/raw/playlists.json"
SUMMARY_FILE_PATH = Path("data/processed/playlist_df.csv")
PLAYLIST_DF = pd.read_csv(SUMMARY_FILE_PATH, index_col=0)
PLAYLIST_DF_UL = PLAYLIST_DF.drop(columns=['pid'])


# Unpack playlist json files
def unpack_playlist(json_file):
    """Unpacks a JSON playlist file into a list of playlists.
    Args:
        json_file (str): The path to the JSON file.
    Returns:
        list: A list of playlists.
    """

    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data['playlists']
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error unpacking playlist: {e}")


# Extract playlist ID (pid)  and track_uri of all tracks in the playlists
def find_track_uris(playlists, start=0, end=SIZE):
    """Finds the track URIs for a given range of playlists.
    Args:
        playlists (list): A list of playlists.
        start (int): The starting index of the playlists to process.
        end (int): The ending index of the playlists to process (optional).
            en must be inferior to 500
    Returns:
        tuple: A tuple containing a list of track URIs and
        a list of playlist IDs.
    """

    end = min(len(playlists), end)

    track_uris = [[track['track_uri'] for track in playlist['tracks']] for playlist in playlists[start:end]]
    playlist_ids = [playlist['pid'] for playlist in playlists[start:end]]

    return track_uris, playlist_ids


#  Function to extract spotify playlist ID from a spotify playlist url
def extract_spotify_playlist_id(url: str) -> str:
    """Extracts the Spotify playlist ID from a given Spotify playlist URL.

    Args:
        url (str): The Spotify playlist URL.

    Returns:
        str: The Spotify playlist ID. or the index on a json file of playlists

    Raises:
        ValueError: If the URL is not a valid Spotify playlist URL.
    """
    # Regular expression pattern to match Spotify playlist URL format
    pattern_url = r"^https://open\.spotify\.com/playlist/([\w\d]{22})(\?.*)?$"

    # pattern of a number between 1 and 499
    pattern_index = r"^(\b([1-9]|[1-9][0-9]|[1-4][0-9]{2})\b)$"

    # Compile the pattern
    compiled_pattern_url = re.compile(pattern_url)
    compiled_pattern_index = re.compile(pattern_index)

    # Check if the a given playlist URL matches the pattern
    match_url = compiled_pattern_url.match(url)
    match_index = compiled_pattern_index.match(url)

    if bool(match_url):
        # Extract the playlist ID
        # playlist_id = url.split("/")[4].split("?")[0]
        playlist_id = match_url.group(1)
        is_url = 1

    elif bool(match_index):
        playlist_id = int(url)
        is_url = 0

    else:
        raise ValueError("Invalid Spotify playlist URL")

    return is_url, playlist_id


def playlist_summarise(playlist_uri):
    '''
    where we query playlist uris with spotify API
    input: list of uris for a given playlist
    return: the  mean features min max scaled of the given playlist
    '''
    all_key = np.zeros(len(playlist_uri))
    all_acousticness = np.zeros(len(playlist_uri))
    all_danceability = np.zeros(len(playlist_uri))
    all_energy = np.zeros(len(playlist_uri))
    all_instrumentalness = np.zeros(len(playlist_uri))
    all_loudness = np.zeros(len(playlist_uri))
    all_speechiness = np.zeros(len(playlist_uri))
    all_valence = np.zeros(len(playlist_uri))
    all_tempo = np.zeros(len(playlist_uri))

    # unpack each uri
    for i in tqdm(range(len(playlist_uri))):
        # query spotify api
        audio_features = sp.audio_features(playlist_uri[i])
        all_key[i] = audio_features[0]['key']
        all_acousticness[i] = audio_features[0]['acousticness']
        all_danceability[i] = audio_features[0]['danceability']
        all_energy[i] = audio_features[0]['energy']
        all_instrumentalness[i] = audio_features[0]['instrumentalness']
        all_loudness[i] = audio_features[0]['loudness']
        all_speechiness[i] = audio_features[0]['speechiness']
        all_valence[i] = audio_features[0]['valence']
        all_tempo[i] = audio_features[0]['tempo']

        # wait time to manage spotify api rate limit
        if (i+1) % 20 == 0:
            time.sleep(30)

    # calculate means
    key = np.mean(all_key)
    acousticness = np.mean(all_acousticness)
    danceability = np.mean(all_danceability)
    energy = np.mean(all_energy)
    instrumentalness = np.mean(all_instrumentalness)
    loudness = np.mean(all_loudness)
    speechiness = np.mean(all_speechiness)
    valence = np.mean(all_valence)
    tempo = np.mean(all_tempo)

    summary = [
        key, acousticness, danceability, energy,
        instrumentalness, loudness, speechiness,
        valence, tempo
    ]

    return summary


# Retrieve playlist info and tracks given spotify playlist url
def get_playlist_info_from_url(sp, playlist_url):
    """
    Retrieves information on given playlist URL and predict its music genre

    Args:
        sp (spotipy.Spotify): A Spotify client object.
        playlist_ref (str): The Spotify URL of the playlist.
        classifier (object): A trained machine learning classifier.
        genres (list): A list of possible genres.

    Returns:
        tuple: A tuple containing the playlist ID, name, and predicted genre.
    """

    uri_label = playlist_url
    # Retrieve URI and audio features of all tracks in the playlist
    playlist_uris = [i['track']['uri'] for i in sp.playlist(uri_label)['tracks']['items']]
    features = np.array(playlist_summarise(playlist_uris))
    playlist_name = sp.playlist(uri_label)['name']
    print(f'Playlist Name: {playlist_name}')

    print(f"Number of tracks in the playlist: {len(playlist_uris)}")

    return uri_label, playlist_name, features, playlist_uris


def get_playlist_info_from_index(playlist_num):
    """
    Retrieves information about a given playlist, including its ID, name, and predicted genre.

    Args:
        playlist_num (int): The index of the playlist in the playlists list.
        classifier (object): A trained machine learning classifier.
        genres (list): A list of possible genres.

    Returns:
        tuple: A tuple containing the playlist ID, name, and predicted genre.
    """
    playlists = unpack_playlist(JSON_FILE_PATH)
    # print(f"*** lenght of playlists_json: {len(playlists)} ***")  # control
    print(f"*** playlist_num: {playlist_num} ***")  # control
    playlist_id = playlists[playlist_num]['pid']
    playlist_name = playlists[playlist_num]['name']
    print(f"Name of playlist: {playlist_name}")

    features = PLAYLIST_DF_UL.values[playlist_num]

    playlist_uris, _ = find_track_uris(playlists, start=playlist_num-1, end=playlist_num)
    playlist_uris = playlist_uris[0]

    print(f"Number of tracks in the playlist: {len(playlist_uris)}")

    return playlist_id, playlist_name, features, playlist_uris


# Summarizes audio features of a recommended songs.
def summarize_reco_songs(reco_uris, reco_data):
    """
    Summarizes the recommended songs based on their URIs and associated data.

    Args:
        reco_uris: A list of URIs for the recommended songs.
        reco_data: A DataFrame containing information about all songs, including their URIs and other relevant features.

    Returns:
        A DataFrame co
    """

    df_reco = reco_data[reco_data["uri"].isin(reco_uris)]
    df_reco = df_reco.drop(columns=["uri"])
    return df_reco.mean()


# Cosine similarity between two vectors
def cosine_similarity(vector1, vector2):
    """Calculates the cosine similarity between two vectors.
    Args:
        vector1: The first vector.
        vector2: The second vector.
    Returns:
        The cosine similarity between the two vectors.
    """

    dot_product = np.dot(vector1, vector2)
    magnitude1 = np.linalg.norm(vector1)
    magnitude2 = np.linalg.norm(vector2)
    cosine_s = dot_product / (magnitude1 * magnitude2)
    
    return cosine_s


# Evaluate cosine similary between a playlist and recommended songs
def reco_similarity_to_playlist(playlist_summary, recommended_uris, reco_data):
    recommend_songs_summary = summarize_reco_songs(recommended_uris, reco_data)
    similarity_score = cosine_similarity(playlist_summary, recommend_songs_summary)
    
    return similarity_score


def predict_song(playlist_ref):
    """
    Predicts songs similar to a given playlist reference.
    Saves info of playlist submitted and recommended songs to a json file

    Args:
        playlist_ref (str): The reference to the playlist (Spotify URL or index).

    Returns:
        tuple: (playlist_name, predicted_music_genre, list_of_recommended_songs)

    Raises:
        ValueError: If the playlist reference format is invalid.
    """

    # Step 1 - Extract playlist Information
    is_url, playlist_id = extract_spotify_playlist_id(playlist_ref)

    # Fetch playlist data depending on reference type (URL or index)
    if is_url == 1:
        playlist_info = get_playlist_info_from_url(sp, playlist_id)
    elif is_url == 0:
        playlist_info = get_playlist_info_from_index(playlist_id)
    else:
        raise ValueError("Invalid Spotify playlist reference format")

    playlist_id, playlist_name, features, playlist_uris = playlist_info

    # Step 2 - Predict Music Genre

    genres = load_txt(Path("data/to_rec/genres.txt"))
    genres.sort()   # make sure the genres list is sorted

    # Initialize prediction pipeline and predict the playlist's genre
    prediction_pipeline = PredictionPipeline()
    predicted_genre_idx = prediction_pipeline.predict(features.reshape(1, 9))[0]
    
    # genre_idx = genres.index(int(predicted_genre_idx))
    # print(genre_idx)
    predicted_genre = genres[predicted_genre_idx]

    print("----"*5, "Playlist predicted music genre", "---"*5)
    print(predicted_genre)
    print(f"genre_idx: {predicted_genre_idx}") 

    # 3 - Recommend relevent Songs
    genre_songs = pd.read_csv(f"data/to_rec/to_rec_{predicted_genre_idx}.csv")

    # print("***** genres_songs **** \n", genre_songs.info()) # check

    # Initialize recommendation pipeline with predicted genre and playlist features
    recommendation_pipeline = RecommendationPipeline(predicted_genre_idx, features)
    rclasses, recommendation_probabilities = recommendation_pipeline.predict()
    if rclasses.ndim >= 2:
        classes = np.argmax(rclasses, axis=1)
    else:
        classes = rclasses
    # print("===classes, reco_proba===\n",classes, recommendation_probabilities) # control
    #print("=== type(classes)====", type(classes))  # check
    #convert_classes = np.argmax(classes, axis=1)
    #print("=== convert_classes===\n", convert_classes)
    #print("=== type:", type(convert_classes))
    # Get the class with the highest recommendation score
    top_class_idx = recommendation_probabilities.argmax()
    max_value = recommendation_probabilities[top_class_idx]
    
   # print(f"*** Top recommended class index: {top_class_idx} ***")
   # print(f" *** max_value: {max_value} ***")  # control

    # Filter songs belonging to the top recommended class
    recommended_songs_df = genre_songs.loc[np.where(classes == top_class_idx)]

    # print("**** recommended_songs_df **** \n", recommended_songs_df.info()) # check

    # Exclude songs already in the playlist
    recommended_songs_uris = np.setdiff1d(recommended_songs_df['uri'].values, playlist_uris)

    # print("**** recommended_uris **** \n", recommended_songs_uris) # check

    print("----"*5, "recommended songs", "---"*5)

    # Step 4 - Fetch Song Details and Display Recommendations
    recommended_songs = []

    for song_uri in recommended_songs_uris[:20]:
        track_data = sp.track(song_uri)
        track_title = track_data['name']
        artist_name = track_data['artists'][0]['name']
        spotify_track_url = track_data['external_urls']['spotify']

        recommendation = f"{track_title}, by {artist_name}, {spotify_track_url}"
        recommended_songs.append(recommendation)
        print(recommendation)

    # Step 5 - Compute the similarity of recommended songs to the playlist
    recommended_uris = recommended_songs_uris[:20]
    reco_similarity_score = reco_similarity_to_playlist(
                            playlist_summary=features, 
                            recommended_uris = recommended_uris, 
                            reco_data=recommended_songs_df
                        )
    print("----"*5, "similarity_score", "---"*5)
    print(f"similarity_score: {reco_similarity_score}")

    # Step 6 - Save Recommendation Data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_reco_filename = f"reco_{timestamp}.json"
    saved_reco_path = Path(os.path.join("data/reco/", saved_reco_filename))

    recommendation_data = {
        "timestamp": timestamp,
        "playlist_id": playlist_id,
        "reco_similarity_score": reco_similarity_score,
        "is_spotify_url": is_url,
        "playlist_name": playlist_name,
        "predicted_genre": predicted_genre,
        "playlist_tracks": playlist_uris,
        "playlist_summary": list(features),
        "recommended_uris": list(recommended_songs_uris[:20])[:20]
    }

    save_json(saved_reco_path, recommendation_data)
    
    print("----"*5, "END", "---"*5)
    
    # return the playlist name,  predicted music genre and the recommended songs
    return playlist_name, predicted_genre, recommended_songs, reco_similarity_score



if (__name__ == "__main__"):

    pl_ref = "https://open.spotify.com/playlist/37i9dQZF1EVJHK7Q1TBABQ?si=EgeiRG8GRi-NMcXb0YumiA"
    # pl_ref = "https://open.spotify.com/playlist/37i9dQZF1DWV5sGFwUJeqR?si=rzhpTnO8RyixPIP9m9N4lA"
    # print(extract_spotify_playlist_id(pl_ref))

    # pl_ref = "452"
    predict_song(pl_ref)
