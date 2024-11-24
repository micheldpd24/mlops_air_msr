import os
import json
import pandas as pd
import plotly.express as px

from jinja2 import Template

import sys
from pathlib import Path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

# Merge all recommendations data
def merge_reco_data():
    """
    Merges all JSON files in a directory into a single list of dictionaries.
    Args:
        directory: The directory containing the JSON files.
    Returns:
        A list of dictionaries containing the merged data.
    """
    
    directory = "data/reco"
    file_path = "data/reco/recommendation_data.json"
    
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump([], f)  # Créer un fichier JSON vide avec une liste vide
        print(f"{file_path} created with success")

    with open(file_path, "r") as f:
        merged_data = json.load(f)

    for filename in os.listdir(directory):
        
        if filename.startswith("reco_") and filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            
            with open(filepath, "r") as f:
                data = json.load(f)
                merged_data.append(data)
            
            os.remove(filepath)  # Delete processed file

    with open("data/reco/recommendation_data.json", "w") as f:
        json.dump(merged_data, f, indent=4)
        
    return merged_data


# Trend of cosine similarity beetween playlists and recommendations
# Version Plotly
def cosine_similarity_trend(rolling_window=5):
    data = merge_reco_data()
    df = pd.DataFrame(data)
    df["rolling_mean"] = df["reco_similarity_score"].rolling(window=rolling_window).mean()

    # Créer un graphique interactif avec Plotly
    fig = px.bar(df, x="timestamp", y="reco_similarity_score", color="predicted_genre", title="Cosine Similarity over time",
                  labels={"reco_similarity_score": "Cosine Similarity", "timestamp": "Date"})
    

    # Ajouter une ligne pour la moyenne mobile
    data = df[["timestamp", "rolling_mean"]]
    fig.add_scatter(x=data["timestamp"], y=data["rolling_mean"], mode='markers', name='Rolling Mean')

    # Ajouter une ligne horizontale rouge à y=0.15
    fig.add_hline(y=0.15, line=dict(color='red', dash='dash'))

    # Enregistrer le graphique interactif sous forme de fichier HTML
    #fig.write_html("src/app/templates/reco_monitoring.html")
    
    # Convert graph to html code
    graph_html = fig.to_html(full_html=False)
    
    # fig.show()
    return graph_html


if (__name__ == "__main__"):

    cosine_similarity_trend(rolling_window=5)