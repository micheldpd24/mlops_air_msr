import os
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from src.entity import ModelTrainerConfig


class ModelTrainer:
    def __init__(self, config: ModelTrainerConfig):
        self.config = config

    def train(self):
        data_train = pd.read_csv(self.config.X_train_path)
        target_train = pd.read_csv(self.config.y_train_path)
        X_train =data_train.values
        y_train = target_train.values.ravel()

        gb = GradientBoostingClassifier(
            learning_rate=self.config.learning_rate,
            max_depth=self.config.max_depth,
            n_estimators = self.config.n_estimators,
            random_state=42
        )
        gb.fit(X_train, y_train)

        joblib.dump(
            gb, os.path.join(
                self.config.root_dir, 
                self.config.model_name
            )
        )