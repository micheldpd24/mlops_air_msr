import os
from pathlib import Path
import sys
# Add parent directory to path
parent_folder = Path(__file__).parent.parent
sys.path.append(str(parent_folder))

from custom_logger import logger

def set_retrain_env():
    # Chemin vers le fichier retrain.log
    log_file = "data/raw/retrain.log"

    # Vérifier si le fichier retrain.log existe
    if os.path.isfile(log_file):
        # Ouvrir et lire le fichier
        with open(log_file, 'r') as file:
            # Chercher la ligne commençant par "RETRAIN="
            for line in file:
                if line.startswith('RETRAIN='):
                    # Extraire la valeur après "RETRAIN="
                    retrain_value = line.strip().split('=')[1]
                    # Définir la variable d'environnement RETRAIN
                    os.environ['RETRAIN'] = retrain_value
                    print(f"RETRAIN environment variable set to: {retrain_value}")
                    logger.info(f"RETRAIN environment variable set to: {retrain_value}")
                    return retrain_value
        logger.info("RETRAIN not found")
        return None 
    else:
        print("! Retrain.log file not found !")
        logger.info("! Retrain.log file not found !")
        return None

if __name__ == "__main__":
    retrain_value = set_retrain_env()

    # Si RETRAIN == 1, exécuter le script Python src/main.py
    if retrain_value == '1':
        print("retrain value == 1")
        logger.info(f"retrain value = {retrain_value}")     
        
        logger.info("Execute the pipeline") 
        os.system('python src/main.py')
        
        logger.info("Reset retrain value to 0")  
        with open('data/raw/retrain.log', 'w') as f:
            f.write('RETRAIN=0')
    
    else:
        print("No action to do")
        logger.info(f"retrain value = {retrain_value}. No action to do")
