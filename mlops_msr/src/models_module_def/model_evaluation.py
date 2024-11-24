import pandas as pd
from time import time
from datetime import datetime
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.models import infer_signature
import mlflow.sklearn
import joblib
from pathlib import Path
from urllib.parse import urlparse
from sklearn.metrics import accuracy_score, classification_report
import os
import sys
from pathlib import Path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

from custom_logger import logger
from src.entity import ModelEvaluationConfig
from src.common_utils import save_json


class ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig):
        self.config = config
        
    def eval_metrics(self, actual, pred):
        accuracy = accuracy_score(actual, pred)
        cl_report = classification_report(actual, pred)
        
        print("Classification Report:")
        print(cl_report)
        logger.info(f"Accuracy: {accuracy}")
        logger.info(f"Classification Report:\n {cl_report}")
        
        return accuracy
    
    def log_into_mlflow(self):
        
        X_test = pd.read_csv(self.config.X_test_path)
        y_test = pd.read_csv(self.config.y_test_path)
        
        X_test = X_test.values
        y_test = y_test.values.ravel()
        
        model = joblib.load(self.config.model_path)

        mlflow.set_registry_uri(self.config.mlflow_uri)
        # tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme

        mlflow.set_experiment(experiment_name="music_clf")
        mlflow.set_experiment_tag('mlflow.note.content', "Song classification by music genre")

        with mlflow.start_run():

            t0 = time()
            predicted_genres = model.predict(X_test)
            time_predict = time() - t0

            accuracy = self.eval_metrics(y_test, predicted_genres)

            # Saving metrics as local
            scores = {"accuracy": accuracy, "time_predict": time_predict}
            save_json(path=Path(self.config.metric_file_name), data=scores)

            mlflow.log_params(self.config.all_params)
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("time_predict", time_predict)
            signature = infer_signature(X_test, model.predict(X_test))
            
            print("*** starting log_model: Music Classification ***")  # Control
            logger.info("start log_model: Music Classification")
            mlflow.sklearn.log_model(
                    model, 
                    "GB_model", 
                    signature=signature
            )


    def get_best_clf_model(self):
        """
        Retrieves the MLflow run with the best score for a specified metric and loads the associated model.
        
        Args:
            experiment_name (str): The name of the MLflow experiment.
            metric (str): The metric used to determine the best model. Default is "accuracy".
        
        Returns:
            tuple: A tuple containing:
                - loaded_model: The MLflow model object.
                - best_run_id (str): The ID of the best run.
                - best_metric_value (float): The value of the best metric.
        
        Raises:
            ValueError: If the experiment or runs are not found.
        """

        experiment_name = "music_clf"
        model = "GB_model"
        metric = "accuracy"

        # Initialize the MLflow client
        client = MlflowClient()

        # Get the experiment details
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            raise ValueError(f"Experiment '{experiment_name}' not found!")
        
        # Fetch all runs for the experiment
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="",
            run_view_type=mlflow.entities.ViewType.ACTIVE_ONLY,
            order_by=[f"metrics.{metric} DESC"]  # Order by the specified metric in descending order
        )
        
        if not runs:
            raise ValueError(f"No runs found for experiment '{experiment_name}'!")
        
        # Extract the best run
        best_run = runs[0]
        best_run_id = best_run.info.run_id
        best_metric_value = best_run.data.metrics[metric]
        
        print(f"Best Run ID: {best_run_id}")
        print(f"Best {metric.capitalize()}: {best_metric_value}")
        logger.info(f"Best Run ID: {best_run_id}")
        logger.info(f"Best {metric.capitalize()}: {best_metric_value}")
        
        # Load the model associated with the best run
        model_uri = f"runs:/{best_run_id}/{model}"
        loaded_model = mlflow.pyfunc.load_model(model_uri)
        
        print(f"Best {experiment_name} model loaded successfully!")
        logger.info(f"Best {experiment_name} model loaded successfully!")
        
        # save the model
        best_model_path = "models_best/gb_model.joblib"
        joblib.dump(loaded_model, best_model_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        best_data = {
            "timestamp": timestamp,
            "experiment_name": experiment_name,
            "run_id": best_run_id,
            "model": model, 
            "model_uri": model_uri, 
            "metric": metric, 
            "metric_value": best_metric_value
        }
        best_data_path = os.path.join("data/models_best", f"{experiment_name}_best_model_{timestamp}.json")
        save_json(Path(best_data_path), best_data)
        print(f"Best {experiment_name} model saved successfully!")
        logger.info(f"Best {experiment_name} model saved successfully!")
        


