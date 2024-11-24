import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from custom_logger import logger
from src.entity import DataTransformationConfig

class DataTransformation:
    def __init__(self, config: DataTransformationConfig):
        self.config = config

    def train_test_splitting(self): 
        data = pd.read_csv(self.config.data_path, index_col=0)
        # data = pd.read_csv(os.path.join(self.config.root_dir, "data_scaled.csv"), index_col=0)

        X = data.drop(columns=["uri", "genre"])
        y = data["genre"]
        check = pd.DataFrame()  # control
        check["genre"] = data["genre"]  # control
        
        # Label encoder
        le = LabelEncoder()
        le.fit(y)
        y = le.transform(y)
        y = pd.DataFrame(y)
        
        check["label"] = y  # control
        print(check.value_counts())  # control
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        X_train.to_csv(os.path.join(self.config.root_dir, "X_train.csv"), index = False)
        y_train.to_csv(os.path.join(self.config.root_dir, "y_train.csv"), index = False)
        X_test.to_csv(os.path.join(self.config.root_dir, "X_test.csv"), index = False)
        y_test.to_csv(os.path.join(self.config.root_dir, "y_test.csv"), index = False)

        logger.info("Splitted data into training and test datasets")
        logger.info(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
        logger.info(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")

        print(X_train.shape, y_train.shape)
        print(X_test.shape, y_test.shape)

    # split data by music genre and save list of music genre into a txt file
    def split_by_genre(self):
        
        data = pd.read_csv(self.config.data_path, index_col=0)
        genres = self.config.genres

        with open(os.path.join(self.config.reco_dir, "genres.txt"), "w") as f:
            f.write("\n".join(genres))
        
        logger.info(f"List of music genres savec into genre.txt")

        for i, genre in enumerate(genres):
            data_genre = data[data["genre"] == genre]
            data_genre = data_genre.drop(columns = ["genre"]).reset_index(drop=True)
            data_genre.to_csv(os.path.join(self.config.reco_dir, f"to_rec_{i}.csv"), index = False)
            
            logger.info(f"{genre} music data extracted")
            logger.info(f"{genre}_data shape: {data_genre.shape}")
    
        logger.info(f"Songs data splitted by music genres")
