[[_TOC_]] 

# Dagster Pipeline Example

A boilerplate for creating data pipelines using Dagster, Docker, and Poetry. To use this repo, fork it and follow the instructions below
## Features
* **Picks up code changes immediately** (just hit `Reload` in dagit; don't have to restart the container!)
* **Unified Dockerfile for development & deployment; easily integrates with CI/CD processes**
* **Packages the source code according to PEP517 & PEP518**
* **Tractable package management. No more hideous `pip freeze > requirements.txt`**
# Setup (using a container)

## Build and Run Dagster

``` bash
docker compose down  # if already running
docker compose build
docker compose up
```

**Done!** At this point, you should be able to successfully navigate to the [Dagit UI](https://localhost:3000) and launch the job
## Configure Slack (optional)
The `top_hacker_news` job will run out of the box and simply log its results to console, but if you [configure a Slack Webhook](https://api.slack.com/messaging/webhooks), the job will send its output to the corresponding channel, which is much more fun :)

After creating the Slack Webhook, copy the Slack Webhook URL and uncomment the environment variable lines in [`docker-compose.yml`](docker-compose.yml), then restart the container

## Install Poetry (optional)
When using containerization, installing poetry locally is not necessary, but it is recommended; the venv it creates can be used for code completion, simple interactive debugging, and more

* Install [python 3.9](https://www.python.org/downloads/release/python-398/)
* Install [poetry](https://python-poetry.org/docs/)

# Alternative Setup (no container)
The alternative setup runs locally without any containerization

> **Note** It's recommended that the application is run using the [docker approach](#setup-using-a-container)
## Run Dagster Locally
Running locally is very similar to using the container

1. [Install poetry](#install-poetry-optional) (not optional in this case)
2. Export the [environment variable(s)](#configure-slack-optional)
3. Open a terminal in the project root and run the following commands

``` bash

# First command optional. creates `.venv` in the project root; very useful when using VSCode!
poetry config virtualenvs.in-project true
poetry install
# To use poetry (i.e. activate the virtualenv):
poetry shell
dagit -w workspace.yaml
```

# FAQ
## During Development, When Should I Rebuild/Restart the Docker Container?
If you change any env vars or files that are **outside of `job_configs` or `src`**, then you'll want to rebuild the docker container, e.g. when...
* adding new packages to `pyproject.toml`
* modifying `Dockerfile`
* adding a volume mount for DAGSTER_HOME

## How Do I Install Python Packages?
Just add it to `[tool.poetry.dependencies]` in [pyproject.toml](pyproject.toml) (or `[tool.poetry.dev-dependencies]`) and rebuild the container. If using poetry locally without containerization, also run `poetry update` to update the lockfile

## Poetry Doesn't Like My Lock File. What do I do?
Don't worry! Delete `poetry.lock`(poetry.lock) and run `poetry install` locally to recreate it
## Does This Approach Work for Dagster Daemon?
Yes! If you're developing sensors, partitions, schedules, and want to test them in your container, then simply uncomment the following line in the `dev` stage of the Dockerfile:
```
# RUN echo "poetry run dagster-daemon run &" >> /usr/bin/dev_command.sh
```

## How Do I Deploy This Repo through CI/CD?
I leave this as an exercise for the reader and/or the reader's DevOps team :) Though here are some tips:
* Use semantic versioning to version-bump `pyproject.toml` and associate this with the container version
* You don't need to target a specific stage in the Dockerfile; the end result is a Dagster User Code Deployment in a ready-to-use container
* If using helm, make sure you've added the correct container version to the list of User Code Deployments; don't forget to apply any secrets/env vars as needed
