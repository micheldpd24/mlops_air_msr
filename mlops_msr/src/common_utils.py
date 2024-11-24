import os
import glob
from box.exceptions import BoxValueError
import yaml
from custom_logger import logger
import json
import joblib
from ensure import ensure_annotations
from box import ConfigBox
from pathlib import Path
from typing import Any
import shutil
from box.exceptions import BoxValueError

@ensure_annotations
def read_yaml(path_to_yaml: Path) -> ConfigBox:
    """reads yaml file and returns

    Args:
        path_to_yaml (str): path like input

    Raises:
        ValueError: if yaml file is empty
        e: empty file

    Returns:
        ConfigBox: ConfigBox type
    """
    try:
        with open(path_to_yaml) as yaml_file:
            content = yaml.safe_load(yaml_file)
            logger.info(f"yaml file: {path_to_yaml} loaded successfully")
            return ConfigBox(content)
    except BoxValueError:
        raise ValueError("yaml file is empty")
    except Exception as e:
        raise e
    

@ensure_annotations
def create_directories(path_to_directories: list, verbose=True):
    """create list of directories

    Args:
        path_to_directories (list): list of path of directories
        ignore_log (bool, optional): ignore if multiple dirs is to be created. Defaults to False.
    """
    for path in path_to_directories:
        os.makedirs(path, exist_ok=True)
        if verbose:
            logger.info(f"created directory at: {path}")


@ensure_annotations
def save_json(path: Path, data: dict):
    """save json data

    Args:
        path (Path): path to json file
        data (dict): data to be saved in json file
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    logger.info(f"json file saved at: {path}")


@ensure_annotations
def load_json(path: Path) -> ConfigBox:
    """load json files data

    Args:
        path (Path): path to json file

    Returns:
        ConfigBox: data as class attributes instead of dict
    """
    with open(path) as f:
        content = json.load(f)

    logger.info(f"json file loaded succesfully from: {path}")
    return ConfigBox(content)


@ensure_annotations
def load_txt(path: Path):
    """Loads data from a text file into a list.
    Args:
        file_path: The path to the text file containing the genres.
    Returns:
        A list of lines content of the txt file.
    """

    data = []
    with open(path, 'r') as f:
        for line in f:
            x = line.strip()
            if x:
                data.append(x)

    logger.info(f"text file loaded succesfully from: {path}")
    
    return data


# function to move file to .archives folder
def move_file_to_archives(file_path: str):
    """
    Moves a specified file to the .archives directory in its current location.
    """
    file = Path(file_path)
    archives_dir = file.parent / ".archives"
    archives_dir.mkdir(exist_ok=True)  # Create .archives if it doesn't exist
    shutil.move(str(file), archives_dir / file.name)


# function to delete all file into a given directory
def delete_csv_files(directory):
    # Pattern to find all .csv files in the directory
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    
    # Delete each .csv file
    for file_path in csv_files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")


def delete_folder(folder_path):
    """
    Deletes the folder at the specified path. This will delete the folder and all of its contents.

    Args:
    folder_path (str): The path to the folder that should be deleted.
    """
    try:
        # Check if the folder exists before attempting to delete
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)  # Recursively delete the folder and its contents
            print(f"The folder {folder_path} has been deleted.")
        else:
            print(f"The folder {folder_path} does not exist or is not a valid directory.")
    except Exception as e:
        print(f"Error deleting the folder {folder_path}: {e}")




