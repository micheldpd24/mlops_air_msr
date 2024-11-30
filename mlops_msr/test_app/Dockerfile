# Image légère
FROM python:3.11.10-slim

# Répertoire de travail
WORKDIR /app

# Copie dans le conteneur
COPY routes_test.py .

# Installations des dépendances
RUN pip install requests tinydb

# Exécution du script python qui lance les requêtes
CMD ["python", "/app/routes_test.py"]

