import joblib
import mlflow
import pandas as pd
from pathlib import Path
from joblib import dump
from mlflow.models import infer_signature
from mlflow.pyfunc import PythonModel

class PredictionPipeline:
    def __init__(self):
        # self.model = joblib.load(Path("models/model.joblib"))
        self.model = joblib.load(Path("models_best/gb_model.joblib"))
        # self.model = mlflow.pyfunc.load_model(Path("models_best/gb_model.joblib"))

    def predict(self, data):
        prediction = self.model.predict(data)
        return prediction


class RecommendationPipeline:
    def __init__(self, class_num, features):
        self.class_num = class_num
        self.features = features
        self.data = pd.read_csv(Path(f"data/to_rec/to_rec_{class_num}.csv"))
        # for pipeline
        # self.model = mlflow.pyfunc.load_model(Path(f"models/pyfunc_gm_model_{class_num}")) 
        # for best model 
        self.model = mlflow.pyfunc.load_model(f"models_best/gm_model_{class_num}")       


    def predict(self):
        song_data = self.data.drop(columns=["uri"]).values
        classes = self.model.predict(song_data, params={"predict_method": "predict"})
        features = self.features
        # reco = self.model.predict_proba(features.reshape(1, -1))[0]
        reco = self.model.predict(features.reshape(1, -1))[0]

        return classes, reco

