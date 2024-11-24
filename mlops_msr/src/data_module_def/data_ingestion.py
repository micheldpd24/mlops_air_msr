import os
import pandas as pd
import urllib.request as request
import zipfile
from pathlib import Path
from src.entity import DataIngestionConfig
from custom_logger import logger

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config
        
    def download_file(self):
        if not os.path.exists(self.config.local_data_file):
            filename, headers = request.urlretrieve(
                url = self.config.source_url,
                filename = self.config.local_data_file
            )
            logger.info(f"{filename} download! With following info: \n{headers}")
        
        else:
            logger.info(f"File already exists.")

    def extract_zip_file(self):
        """
        zip_file_path: str
        Extracts the zip file into the data directory
        Function returns None
        """

        unzip_path = self.config.unzip_dir
        os.makedirs(unzip_path, exist_ok=True)
        with zipfile.ZipFile(self.config.local_data_file, 'r') as zip_ref:
            zip_ref.extractall(unzip_path)
    
    def make_data(self):
        unzip_path = self.config.unzip_dir
        raw_data_path = f"{unzip_path}/dataset.csv"
        df0 = pd.read_csv(raw_data_path, index_col=0)
        
        df0.rename(columns={"track_id": "uri",  "track_genre": "genre"}, inplace=True)
        
        columns_to_drop = ["artists", "album_name", "track_name", "popularity", "explicit", 
                           "time_signature", "duration_ms", "mode", "liveness"]
        
        df0.drop(columns=columns_to_drop, axis=1, inplace=True)

        df0.dropna(inplace=True, ignore_index=True)
        
        genres = ['alternative', 'classical', 'country', 'edm', 'hip-hop', 
                  'jazz', 'latin', 'pop', 'r-n-b', 'rock']
        
        df = df0[df0["genre"].isin(genres)].reset_index(drop=True)

        df.drop_duplicates(subset=["uri"], inplace=True, ignore_index=True)

        print(df.info())
        print(df.head())

        df.to_csv("data/raw/song_df.csv")

    def get_data(self):
        """Main function to trigger the download, extraction, and data processing."""
        
        # check if song_df exists in "data/raw"
        path_file = os.path.join(self.config.root_dir, "song_df.csv")
        if Path(path_file).exists():
            print("Retraining mode - No need to download and extract the dataset again.")
            logger.info("Retraining mode - No need to download and extract the dataset again.")
        else:
            print("Extracting and preparing dataset")
            logger.info("Extracting and preparing dataset")  
            self.download_file()
            self.extract_zip_file()
            self.make_data()

