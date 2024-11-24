# Use the official Python 3.11.10 image as a base
FROM python:3.11.10-slim

# Set the working directory
WORKDIR appli/

# Create a volume at /data
VOLUME /appli/data

# Copy the requirements file
COPY ../app_requirements.txt ./

# Install any required packages
RUN pip install --no-cache-dir -r app_requirements.txt

# Install dependencies in one step to reduce the number of layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    git \
 && pip install --no-cache-dir -r app_requirements.txt \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

 # Copy necessary directories and files
COPY data data
# COPY dataset dataset
COPY logs logs
COPY metrics metrics
COPY models models
COPY models_best models_best
COPY shell_scripts_dk scripts
COPY src src
COPY users users
COPY users users
COPY main.py custom_logger.py ./
# COPY .env custom_logger.py dvc.yaml dvc.lock ./
# COPY main.py ./
COPY __init__.py ./

# Ensure the scripts are executable
RUN chmod +x scripts/*.sh

# Expose port 5006 for the Flask application
EXPOSE 5000

# Run the recommendation app
CMD ["python", "src/app/app.py"]