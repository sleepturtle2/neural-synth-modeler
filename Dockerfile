FROM python:3.9-slim

# System dependencies
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better Docker cache
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the code
COPY . /app

# Install your package in editable mode
RUN pip install -e .

# Expose BentoML port
EXPOSE 3000

# Change to the neural_synth_modeler directory and build the Bento
WORKDIR /app/neural_synth_modeler
RUN bentoml build

# Start the BentoML service
CMD ["bentoml", "serve", "neural_synth_modeler_service:latest", "--port", "3000"]