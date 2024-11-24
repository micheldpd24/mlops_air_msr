from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    source_url: str
    local_data_file: Path
    unzip_dir: Path

@dataclass(frozen=True)
class DataValidationConfig:
    root_dir: Path
    STATUS_FILE: str
    unzip_data_dir: Path
    all_schema: dict

@dataclass(frozen=True)
class DataTransformationConfig:
    root_dir: Path
    data_path: Path
    reco_dir: Path
    genres: list

@dataclass(frozen=True)
class ModelTrainerConfig:
    root_dir: Path
    X_train_path: Path
    y_train_path: Path
    X_test_path: Path
    y_test_path: Path
    model_name: str
    learning_rate: float
    max_depth: int
    n_estimators: int

@dataclass(frozen=True)
class ModelEvaluationConfig:
    root_dir: Path
    X_test_path: Path
    y_test_path: Path
    model_path: Path
    metric_file_name: Path
    all_params: dict
    mlflow_uri: str

@dataclass(frozen=True)
class UnsModelFitConfig:
    root_dir: Path
    features_path_prefix: str
    genres_path: Path
    model_dir: Path
    model_name_prefix: str
    metrics_path_prefix: str
    all_params: dict
    mlflow_uri: str
