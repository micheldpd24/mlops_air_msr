from src.config import CONFIG_FILE_PATH, SCHEMA_FILE_PATH, PARAMS_FILE_PATH
from src.common_utils import read_yaml, create_directories
from src.entity import (DataIngestionConfig,
                        DataValidationConfig,
                        DataTransformationConfig,
                        ModelTrainerConfig,
                        ModelEvaluationConfig,
                        UnsModelFitConfig)


class ConfigurationManager:
    def __init__(
        self,
        config_filepath = CONFIG_FILE_PATH,
        params_filepath = PARAMS_FILE_PATH,
            schema_filepath = SCHEMA_FILE_PATH):

            self.config = read_yaml(config_filepath)
            self.params = read_yaml(params_filepath)
            self.schema = read_yaml(schema_filepath)

            
    def get_data_ingestion_config(self) -> DataIngestionConfig:
          config = self.config.data_ingestion

          create_directories([config.root_dir])

          data_ingestion_config = DataIngestionConfig(
                root_dir= config.root_dir,
                source_url=config.source_URL,
                local_data_file=config.local_data_file,
                unzip_dir=config.unzip_dir
          )

          return data_ingestion_config
    
    def get_data_validation_config(self) -> DataValidationConfig:
        config = self.config.data_validation
        schema = self.schema.COLUMNS

        create_directories([config.root_dir])

        data_validation_config = DataValidationConfig(
            root_dir = config.root_dir,
            STATUS_FILE = config.STATUS_FILE,
            unzip_data_dir = config.unzip_dir,
            all_schema = schema,
        )

        return data_validation_config
    
    def get_data_transformation_config(self) -> DataTransformationConfig:
          config = self.config.data_transformation

          create_directories([config.root_dir])
          create_directories([config.reco_dir])

          data_transformation_config = DataTransformationConfig(
                root_dir = config.root_dir,
                data_path =  config.data_path,
                reco_dir = config.reco_dir,
                genres = config.genres
          )

          return data_transformation_config
    
    def get_model_trainer_config(self) -> ModelTrainerConfig:
          config = self.config.model_trainer
          params = self.params.GradientBoostingClassifier
          
          create_directories([config.root_dir])

          model_trainer_config = ModelTrainerConfig(
                root_dir = config.root_dir,
                X_train_path = config.X_train_path,
                y_train_path = config.y_train_path,
                X_test_path = config.X_test_path,
                y_test_path = config.y_test_path,
                model_name = config.model_name,
                learning_rate = params.learning_rate,
                max_depth = params.max_depth,
                n_estimators = params.n_estimators
          )

          return model_trainer_config
    
    def get_model_evaluation_config(self) -> ModelEvaluationConfig:
          config = self.config.model_evaluation
          params = self.params.GradientBoostingClassifier

          create_directories([config.root_dir])
          
          model_evaluation_config = ModelEvaluationConfig(
                root_dir=config.root_dir,
                X_test_path = config.X_test_path,
                y_test_path = config.y_test_path,
                model_path=config.model_path,
                metric_file_name=config.metric_file_name,
                all_params=params,
                mlflow_uri="https://dagshub.com/micheldpd24/mlflow_tracking.mlflow", # make sure to update this information
          )

          return model_evaluation_config
    
    def get_unsmodel_fit_config(self) -> UnsModelFitConfig:
          config = self.config.unsmodel_fit
          params = self.params.GaussianMixture
          
          create_directories([config.root_dir])

          unsmodel_fit_config = UnsModelFitConfig(
                root_dir = config.root_dir,
                features_path_prefix = config.features_path_prefix,
                genres_path = config.genres_path,
                model_dir = config.model_dir,
                model_name_prefix = config.model_name_prefix,
                metrics_path_prefix = config.metrics_path_prefix,
                all_params=params,
                mlflow_uri="https://dagshub.com/micheldpd24/mlflow_tracking.mlflow" # make sure to update this information
          )

          return unsmodel_fit_config