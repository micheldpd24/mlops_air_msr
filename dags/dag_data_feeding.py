
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
import time
from datetime import datetime, timedelta

import os
import subprocess
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# from custom_logger import logger

# -------
from pathlib import Path
# import sys
# # Add parent directory to path
# parent_folder = Path(__file__).parent.parent
# sys.path.append(str(parent_folder))

# --------

from dag_utils import(
    load_txt, move_file_to_archives, navigate_between_folders, 
    delete_csv_files, delete_folder, get_most_recent_file, 
    archive_old_file, log_retrain_signal,
    get_genre_uris, get_audio_features, get_genre_songs_features,
    get_all_genres_features, process_song_data,
    run_stage
)

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

# Pipeline Directory
# DIR_STEPS = Path("mlops_msr/src/pipeline_steps")

# Initialize Spotipy client
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)


# Check if the song base is initalized if not run the pipeline first
def check_songs_base_init():
    file_path = "data/raw/song_df.csv"
    if os.path.isfile(file_path):
        return "get_songs_from_spotify"  # Task ID for data acquisition
    else:
        return "data_processing"  # Task ID for model retraining


# function to get songs
def get_songs_from_spotify():    
    get_all_genres_features()
    process_song_data()


# # Add new song into current songs base
# def update_songs_base():
#     """Main function to update the songs database."""
    
#     # logger.info("Starting process_and_merge_song_data")
#     print("Starting songs base update")
    
#     # Step 1: Load the current song data
#     df_old = pd.read_csv("data/raw/song_df.csv", index_col=0)
#     n_songs_old = len(df_old)
    
#     # Step 2: Load the most recent interim file
#     interim_directory = "data/interim"
#     most_recent_file = get_most_recent_file(interim_directory, prefix="song_df", extension=".csv")
#     df_to_add = pd.read_csv(os.path.join(interim_directory, most_recent_file), index_col=0)

#     # Step 3: Concatenate old and new data and remove duplicates
#     df_new = pd.concat([df_old, df_to_add], axis=0, ignore_index=True)
#     df_new = df_new.drop_duplicates(subset=["uri"], ignore_index=True)  # Supprimer les doublons en fonction de la colonne "uri"

#     # Step 4: Save the updated songs data
#     df_new.to_csv("data/new/song_df.csv")
#     print("New songs base saved to data/new/song_df.csv")

#     # Step 5: Calculate the number of songs and delta (percentage change)
#     n_songs_new = len(df_new)
#     delta = (n_songs_new - n_songs_old) / n_songs_old if n_songs_old > 0 else float('inf')
#     print(f"Current number of songs: {n_songs_old}")
#     print(f"New number of songs: {n_songs_new}")
#     print(f"delta: {delta * 100: .2f}%")
#     # logger.info(f"delta: {delta * 100: .2f}%")
    
#     # Step 6: If new songs are added, perform archiving and update the raw songs base
#     if delta > 0.01:
#         print("Delta > 1%. Songs data increase")
#         # logger.info("Delta > 1%. Songs data increase")
        
#         # Archive the old data
#         archive_path_old = archive_old_file("data/raw/song_df.csv", "data/raw")
#         archive_path_new = archive_old_file("data/new/song_df.csv", "data/new")
        
#         # Replace the old song base with the new data
#         df_new.to_csv("data/raw/song_df.csv")
#         print(f"New data info :\n {df_new.info()}")
        
#         # Log retrain_signal
#         log_retrain_signal()

#         print("New data loaded in the pipeline.")
#         print(f"New data info :\n {df_new.info()}")    
#     else:
#         print("No changes in songs base.")
#         # logger.info("No changes in songs base.")
    
#     # implicit push to xcom 
#     return 1 if delta > 0.01 else 0

def update_songs_base(delta_threshold=0.01):
    """Main function to update the songs database with a configurable delta threshold."""
    
    print("Starting songs base update")
    
    # Step 1: Load the current song data
    df_old = pd.read_csv("data/raw/song_df.csv", index_col=0)
    n_songs_old = len(df_old)
    
    # Step 2: Load the most recent interim file
    interim_directory = "data/interim"
    most_recent_file = get_most_recent_file(interim_directory, prefix="song_df", extension=".csv")
    df_to_add = pd.read_csv(os.path.join(interim_directory, most_recent_file), index_col=0)

    # Step 3: Concatenate old and new data and remove duplicates
    df_new = pd.concat([df_old, df_to_add], axis=0, ignore_index=True)
    df_new = df_new.drop_duplicates(subset=["uri"], ignore_index=True)  # Remove duplicates based on "uri"

    # Step 4: Save the updated songs data
    df_new.to_csv("data/new/song_df.csv")
    print("New songs base saved to data/new/song_df.csv")

    # Step 5: Calculate the number of songs and delta (percentage change)
    n_songs_new = len(df_new)
    delta = (n_songs_new - n_songs_old) / n_songs_old if n_songs_old > 0 else float('inf')
    print(f"Current number of songs: {n_songs_old}")
    print(f"New number of songs: {n_songs_new}")
    print(f"Delta: {delta * 100: .2f}%")
    
    # Step 6: If new songs are added, perform archiving and update the raw songs base
    if delta > delta_threshold:
        print(f"Delta > {delta_threshold * 100:.2f}%. Songs data increase")
        
        # Archive the old data
        archive_path_old = archive_old_file("data/raw/song_df.csv", "data/raw")
        archive_path_new = archive_old_file("data/new/song_df.csv", "data/new")
        
        # Replace the old song base with the new data
        df_new.to_csv("data/raw/song_df.csv")
        print(f"New data info :\n {df_new.info()}")
        
        # Log retrain signal
        log_retrain_signal()

        print("New data loaded in the pipeline.")
        print(f"New data info :\n {df_new.info()}")    
    else:
        print("No changes in songs base.")
    
    # Return 1 if delta exceeds the threshold, otherwise return 0
    return 1 if delta > delta_threshold else 0


# check if there are new songs in the songs collected from Spotify
def check_retrain_signal(ti):
    retrain_value = ti.xcom_pull(task_ids=["update_songs_base"])[0]
    if retrain_value == 1:
        return "data_ingestion"
    else:
        return "end"


# pipeline stages
def data_ingestion():
    run_stage("Stage01 Data Ingestion", "stage01_data_ingestion.py")

def data_validation():
    run_stage("Stage02 Data Validation", "stage02_data_validation.py")

def data_transformation():
    run_stage("Stage03 Data Transformation", "stage03_data_transformation.py")

def classification_model_training():
    run_stage("Stage04 Classification Model Training", "stage04_model_trainer.py")

def classification_model_evaluation():
    run_stage("Stage05 Classification Model Evaluation", "stage05_model_evaluation.py")

def clustering_models_fit_and_evaluation():
    run_stage("Stage06 CLustering Models Fit and Evaluation", "stage06_uns_model_fit_eval.py")


# -----------------------------------------------------------------------------#
# ---------------  DAG  DAG  DAG  DAG  DAG  DAG  DAG  DAG  DA -----------------#
# -----------------------------------------------------------------------------#


# Default args
default_args = {
    'owner': 'air-rec-app',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=20),
    'max_active_runs': 1,
}


with DAG(
    'data_feeding_dag',
    default_args=default_args,
    description='run data_feeding.py every hour',
    schedule_interval='20 * * * *',
    start_date=datetime(2024, 11, 21, 15, 0),
    catchup=False,
) as dag:
    

    # Check if the song base is initialized
    check_songs_base_init_task = BranchPythonOperator(
        task_id="check_songs_base_init",
        python_callable=check_songs_base_init,
    )

    # Task group for Spotify data feeding
    with TaskGroup(
        group_id="spotify_data_feed",
        prefix_group_id=False
    ) as tg1_sdf:

        # 2 - Fetch new songs from spotify
        get_songs_from_spotify_task = PythonOperator(
            task_id='get_songs_from_spotify',
            python_callable=get_songs_from_spotify,
            trigger_rule = "none_failed_min_one_success",
        )

        # 3 - Update songs base
        update_songs_base_task = PythonOperator(
            task_id='update_songs_base',
            python_callable=update_songs_base,
            op_kwargs={'delta_threshold': 0.01}
            # trigger_rule = "none_failed_min_one_success",
        )

        get_songs_from_spotify_task >> update_songs_base_task

    # Branching to launch pipleline and end
    check_retrain_signal_task = BranchPythonOperator(
        task_id="check_retrain_signal",
        python_callable=check_retrain_signal,
        trigger_rule = "none_failed_min_one_success",
    )

    with TaskGroup(
        group_id="data_processing",
        prefix_group_id=False
    ) as tg2_dip:
        
        data_ingestion_task = PythonOperator(
            task_id='data_ingestion',
            python_callable=data_ingestion,
            trigger_rule = "none_failed_min_one_success"
        )

        data_validation_task = PythonOperator(
            task_id='data_validation',
            python_callable=data_validation
        )

        data_transformation_task = PythonOperator(
            task_id='data_transformation',
            python_callable=data_transformation
        )
    
        data_ingestion_task >>  data_validation_task >>  data_transformation_task

    
    with TaskGroup(
        group_id="classification_model",
        prefix_group_id=False
    ) as tg3_clf:
        
        classification_model_training_task = PythonOperator(
            task_id='clf_model_training',
            python_callable=classification_model_training
        )

        classification_model_evaluation_task = PythonOperator(
            task_id='clf_model_evaluation',
            python_callable=classification_model_evaluation
        )

        classification_model_training_task >> classification_model_evaluation_task

    
    clustering_model_fit_and_evaluation_task = PythonOperator(
            task_id='clst_model_fit_eval',
            python_callable=clustering_models_fit_and_evaluation
    )
     
    # 6 - end = DummyOperator(task_id='end')
    end = EmptyOperator(task_id='end')


    # Task dependencies
    check_songs_base_init_task >> [tg1_sdf, tg2_dip]
    tg1_sdf >> check_retrain_signal_task >> [tg2_dip, end]
    tg2_dip >> [tg3_clf, clustering_model_fit_and_evaluation_task]
    clustering_model_fit_and_evaluation_task 


    # Task dependencies
    # t0 >> check_songs_base_init_task >> [get_songs_from_spotify_task, launch_pipeline_task]
    # get_songs_from_spotify_task >> update_songs_base_task >> check_retrain_signal_task
    # check_retrain_signal_task >> [launch_pipeline_task, end]
