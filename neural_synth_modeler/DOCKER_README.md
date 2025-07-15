# BentoML Model Server – Docker Usage Guide

This guide explains how to build, run, and manage the BentoML model server using Docker and Docker Compose.

## Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

## 1. Build and Run with Docker Compose

From this directory (`neural_synth_modeler`):

```bash
docker-compose up --build
```
- This builds the Docker image and starts the model server.
- The API will be available at: http://localhost:3000

## 2. Stopping the Server

To stop and remove the container:

```bash
docker-compose down
```

## 3. Build and Run Manually (Optional)

If you prefer to use Docker directly:

### Build the image
```bash
docker build -t neural-synth-model-server .
```

### Run the container
```bash
docker run -p 3000:3000 --name neural-synth-model-server neural-synth-model-server
```

### Stop and remove the container
```bash
docker stop neural-synth-model-server && docker rm neural-synth-model-server
```

## 4. Notes
- The service runs in production mode by default.
- If you change dependencies, rebuild the image with `docker-compose build` or `docker build ...`.
- Logs are shown in the terminal when running with `docker-compose up`.

---

For further customization, edit the `docker-compose.yml` or `Dockerfile` in this directory. 

---

The error:

```
no configuration file provided: not found
```

means that Docker Compose cannot find a `docker-compose.yml` file in your current directory (`neural-synth-modeler`).

From your `ls` output, there is **no `docker-compose.yml` file in this directory**.  
You likely created the file inside the `neural_synth_modeler/neural_synth_modeler` subdirectory, not the project root.

---

## Solution

**Move the file to your current directory:**

Run these commands in your terminal:

```sh
mv neural_synth_modeler/docker-compose.yml .
mv neural_synth_modeler/DOCKER_README.md .
```

Then, verify with:

```sh
ls
```

You should now see `docker-compose.yml` in your current directory.

Now, run:

```sh
docker-compose up --build
```

---

**Summary:**  
Move the `docker-compose.yml` file up one level to your project root, then run your command again.  
If you want, I can provide a one-liner to do this for you! 

---

Your container is crashing with this error:
```
bentoml.exceptions.BentoMLConfigException: BentoML config file specified in ENV VAR does not end with either '.yaml' or '.yml': 'BENTOML_CONFIG=production'
```

**What happened?**
- In your `docker-compose.yml`, you have:
  ```yaml
  environment:
    - BENTOML_CONFIG=production
  ```
- BentoML expects `BENTOML_CONFIG` to point to a YAML config file (e.g., `bentoml_config.yaml`), not just a string like `production`.

---

## How to Fix

**Option 1: Remove the BENTOML_CONFIG environment variable**
- If you don't need a custom config, just remove the `environment:` section from your `docker-compose.yml`.

**Option 2: Point to a valid YAML config file**
- If you want to use a custom config, create a YAML file (e.g., `bentoml_config.yaml`) and set:
  ```yaml
  environment:
    - BENTOML_CONFIG=/app/bentoml_config.yaml
  ```
  (Make sure to copy the file into the image in your Dockerfile.)

---

## Recommended Immediate Fix

Edit your `docker-compose.yml` to remove the `environment:` section entirely:

```yaml
version: '3.8'
services:
  model-server:
    build: .
    container_name: neural-synth-model-server
    ports:
      - "3000:3000"
    restart: unless-stopped
```

Then, re-run:

```sh
docker-compose up --build
```

---

Let me know if you want to use a custom config file, and I can help you set that up! Otherwise, removing the environment variable will resolve the crash. 