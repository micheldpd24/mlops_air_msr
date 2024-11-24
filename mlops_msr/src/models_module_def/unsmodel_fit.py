import os
import pandas as pd
import joblib
from pathlib import Path
from urllib.parse import urlparse
from time import time
from datetime import datetime
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from mlflow.models import infer_signature
from mlflow.pyfunc import PythonModel
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (silhouette_score,
                             calinski_harabasz_score,
                             davies_bouldin_score)
import sys
from pathlib import Path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

from custom_logger import logger
from src.entity import UnsModelFitConfig
from src.common_utils import load_txt, save_json, delete_folder


class UnsModelFit:
    def __init__(self, config: UnsModelFitConfig):
        self.config = config

    def unsfit(self):
        genres = load_txt(Path(self.config.genres_path))

        class ModelWrapper(PythonModel):
            def __init__(self):
                self.model = None


            def load_context(self, context):
                from joblib import load
                self.model = load(context.artifacts["model_path"])

            def predict(self, context, model_input, params=None):
                params = params or {"predict_method": "predict"}
                predict_method = params.get("predict_method")

                if predict_method == "predict":
                    return self.model.predict(model_input)
                elif predict_method == "predict_proba":
                    return self.model.predict_proba(model_input)
                elif predict_method == "predict_log_proba":
                    return self.model.predict_log_proba(model_input)
                else:
                    raise ValueError(f"The prediction method '{predict_method}' is not supported.")

        for element, genre in enumerate(genres):
            try:
                # Load feature file
                features_path = Path(self.config.features_path_prefix+f"{element}.csv")
                if not features_path.exists():
                    print(f"File not found: {features_path}")
                    continue  # Skip this iteration if the file does not exist
                
                features = pd.read_csv(features_path)
                features = features.drop(columns=["uri"], errors="ignore")
                features = features.values
                
                # Initialize Gaussian Mixture Model
                model = GaussianMixture(
                    n_components=self.config.all_params.n_components[element],
                    covariance_type=self.config.all_params.covariance_type,
                    random_state=self.config.all_params.random_state
                )

                # Fit the model
                model.fit(features)
                
                # Save raw model
                
                model_filename = f"{self.config.model_name_prefix}{element}.joblib"
                model_path = os.path.join(self.config.root_dir, model_filename)
    
                joblib.dump(model, model_path)  # save the model to a .joblib file

                # Define artifacts for wrapped model
                artifacts = {"model_path": model_path}

                # Save wrapped PyFunc model
                pyfunc_path = f"models/pyfunc_gm_model_{element}"
                signature = infer_signature(features, params={"predict_method": "predict_proba"}) 
                mlflow.set_registry_uri(self.config.mlflow_uri)
                tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme
                mlflow.set_experiment(experiment_name=f"clst_{element}_{genre}")
                mlflow.set_experiment_tag('mlflow.note.content', f"Clustering {genre} songs with Gaussian Mixture Model")

                delete_folder(pyfunc_path)
                with mlflow.start_run():
                    mlflow.pyfunc.save_model(
                        path=pyfunc_path,
                        python_model=ModelWrapper(),
                        input_example=features,
                        signature=signature,
                        artifacts=artifacts,
                        pip_requirements=["joblib", "sklearn"],
                    )

                    wrapped_model= mlflow.pyfunc.load_model(pyfunc_path)

                    # Save the fitted model
                    model_path = os.path.join(
                                    self.config.root_dir, 
                                    self.config.model_name_prefix+f"{element}.joblib"
                    )
                    joblib.dump(model, model_path)

                    # Prediction and metrics
                    t0 = time()
                    prediction = wrapped_model.predict(features, params={"predict_method": "predict"})
                    time_predict = time() - t0
                    
                    
                    silh_score = silhouette_score(features, prediction)
                    chi_score = calinski_harabasz_score(features, prediction)
                    dab_score = davies_bouldin_score(features, prediction)

                    scores = {
                        "silhouette_score": silh_score,
                        "calinski_harabasz_score": chi_score,
                        "davies_bouldin_score": dab_score,
                        "time_predict": time_predict
                    }

                    metrics_file_path = Path(f"{self.config.metrics_path_prefix}{element}.json")
                    save_json(metrics_file_path, data=scores)

                    # Log metrics and parameters
                    model_params = {
                        "n_components": self.config.all_params.n_components[element],
                        "covariance_type": self.config.all_params.covariance_type,
                        "random_state": self.config.all_params.random_state
                    }
                    
                    mlflow.log_params(model_params)
                    mlflow.log_metric("silhouette_score", silh_score)
                    mlflow.log_metric("calinski_harabasz_score", chi_score)
                    mlflow.log_metric("davies_bouldin_score", dab_score)
                    mlflow.log_metric("time_predict", time_predict)
                    signature = infer_signature(features, wrapped_model.predict(features)) 
                    
                    mlflow.sklearn.log_model(
                                wrapped_model, 
                                "GM_model", 
                                signature=signature,
                    )
                    print(f"Logged model for {genre}: {element}")
                    logger.info(f"Logged model for {genre}: {element}")

            except Exception as e:
                print(f"Error in processing element {element}: {e}")
            
    def get_best_clst_model(self):
        """
        Retrieves the MLflow run with the best score for a specified metric and loads the associated model.
        
        Args:
            experiment_name (str): The name of the MLflow experiment.
            metric (str): The metric used to determine the best model. Default is "accuracy".
        
        Raises:
            ValueError: If the experiment or runs are not found.
        """

        genres = load_txt(Path(self.config.genres_path))
        
        # Initialize the MLflow client
        client = MlflowClient()

        for element, genre in enumerate(genres):
            
            experiment_name = f"clst_{element}_{genre}"
            model = "GM_model"
            metric = "silhouette_score"

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
            
            # Load the model associated with the best run
            model_uri = f"runs:/{best_run_id}/{model}"
            loaded_model = mlflow.pyfunc.load_model(model_uri)
            
            print(f"Best {experiment_name} model loaded successfully!")
            logger.info(f"Best {experiment_name} model loaded successfully!")

            # save the model
            best_model_path = Path(f"models_best/gm_model_{element}")
            delete_folder(best_model_path)
            mlflow.sklearn.save_model(loaded_model, best_model_path)
            
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
            save_json(Path(f"data/models_best/{experiment_name}_best_{timestamp}.json"), best_data)
