import sys
from pathlib import Path

# Add parent directory to path
parent_folder = str(Path(__file__).parent.parent)
sys.path.append(parent_folder)

from custom_logger import logger
from src.pipeline_steps.stage01_data_ingestion import DataIngestionPipeline
from src.pipeline_steps.stage02_data_validation import DataValidationTrainingPipeline
from src.pipeline_steps.stage03_data_transformation import DataTransformationTrainingPipeline
from src.pipeline_steps.stage04_model_trainer import ModelTrainerTrainingPipeline
from src.pipeline_steps.stage05_model_evaluation import ModelEvaluationTrainingPipeline
from src.pipeline_steps.stage06_uns_model_fit_eval import UnsModelFitPipeline

STAGE_NAME = "Data Ingestion stage"
try:
    logger.info(f">>>>> stage {STAGE_NAME} started <<<<<")
    obj = DataIngestionPipeline()
    obj.main()
    logger.info(f">>>>> stage {STAGE_NAME} completed <<<<<\n\nx=======x")
        
except Exception as e:
    logger.exception(e)
    raise e

STAGE_NAME = "Data Validation stage"
try:
    logger.info(f">>>>> stage {STAGE_NAME} started <<<<<")
    obj =  DataValidationTrainingPipeline()
    obj.main()
    logger.info(f">>>>> stage {STAGE_NAME} completed <<<<<\n\nx=======x")
except Exception as e:
    logger.exception(e)
    raise e

STAGE_NAME = "Data Transformation stage"
try:
    logger.info(f">>>>> stage {STAGE_NAME} started <<<<<")
    obj =  DataTransformationTrainingPipeline()
    obj.main()
    logger.info(f">>>>> stage {STAGE_NAME} completed <<<<<\n\nx=======x")
except Exception as e:
    logger.exception(e)
    raise e

STAGE_NAME = "Model trainer stage"
try:
    logger.info(f">>>>> stage {STAGE_NAME} started <<<<<")
    obj = ModelTrainerTrainingPipeline()
    obj.main()
    logger.info(f">>>>> stage {STAGE_NAME} completed <<<<< \n\n x========x")
except Exception as e:
    logger.exception(e)
    raise e

STAGE_NAME = "Model evaluation stage"
try:
    logger.info(f">>>>> stage {STAGE_NAME} started <<<<<")
    obj = ModelEvaluationTrainingPipeline()
    obj.main()
    logger.info(f">>>>> stage {STAGE_NAME} completed <<<<< \n\n x========x")
except Exception as e:
    logger.exception(e)
    raise e

STAGE_NAME = "Unsupervised Model Fit and Evaluation stage"
try:
    logger.info(f">>>>> stage {STAGE_NAME} started <<<<<")
    obj = UnsModelFitPipeline()
    obj.main()
    logger.info(f">>>>> stage {STAGE_NAME} completed <<<<< \n\n x========x")
except Exception as e:
    logger.exception(e)
    raise e
