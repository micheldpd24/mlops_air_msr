import sys
from pathlib import Path

# Add parent directory to path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

from src.config_manager import ConfigurationManager
from src.models_module_def.unsmodel_fit import UnsModelFit
from custom_logger import logger

STAGE_NAME = "Unsupervised Model Fit and Evaluation stage"

class UnsModelFitPipeline:
    def __init__(self):
        pass

    def main(self):
        config = ConfigurationManager()
        unsmodel_fit_config = config.get_unsmodel_fit_config()
        unsmodel_fit = UnsModelFit(config= unsmodel_fit_config)
        unsmodel_fit.unsfit()
        unsmodel_fit.get_best_clst_model()

if __name__ == '__main__':
    try:
        logger.info(f">>>>> stage {STAGE_NAME} started <<<<<")
        obj = UnsModelFitPipeline()
        obj.main()
        logger.info(f">>>>> stage {STAGE_NAME} completed <<<<< \n\n x========x")
    except Exception as e:
        logger.exception(e)
        raise e
