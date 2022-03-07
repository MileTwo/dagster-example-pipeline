###########################################
# dev
###########################################
ARG BASE_IMAGE=python:3.9.8-slim-buster
FROM "${BASE_IMAGE}" as dev

ENV PYTHONUNBUFFERED=True
ENV PIP_NO_CACHE_DIR=True

# Install the python package managers.
RUN pip install -U \
    pip \
    setuptools \
    wheel \
    poetry

# Set this folder at the system root and then cd into it.
WORKDIR /usr/src/app

# Copy poetry's package list and then install all non-developmental dependencies.
COPY poetry.lock pyproject.toml ./

# Installs dependencies, but does *not* install our python code as a package because it's not mounted. Must be added afterward!
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
RUN poetry install 

# Setup a local instance of dagit
RUN mkdir -p /opt/dagster/dagster_home
ENV DAGSTER_HOME=/opt/dagster/dagster_home/

# Using a "heredoc" called `dev_command.sh` because this is the only place and time this script will be needed
RUN echo "poetry install" > /usr/bin/dev_command.sh
RUN echo "poetry run dagster-daemon run &" >> /usr/bin/dev_command.sh
RUN echo "poetry run dagit -h 0.0.0.0 -p 3000" >> /usr/bin/dev_command.sh
RUN chmod +x /usr/bin/dev_command.sh

EXPOSE 3000
CMD ["bash", "dev_command.sh"]

###########################################
# build
###########################################
FROM dev as build

WORKDIR /usr/src/app

# Removes dev dependencies (reuses installed packages from previous docker stage)
RUN poetry install --no-dev

# Copy the contents of the project root directory to the app directory in the container
COPY . .

# Builds our code and dependencies into a python wheel, then saves the resulting name to `package_name`
RUN poetry build --format wheel | grep "Built" | sed 's/^.*\s\(.*\.whl\)/\1/' > package_name

# Override the CMD because we don't really need to run anything here
CMD ["python3"]
###########################################
# deploy
###########################################

FROM "${BASE_IMAGE}"
ARG DAGSTER_VERSION=0.13.19

# ==> Add Dagster layer
RUN \
# Cron
       apt-get update -yqq \
    && apt-get install -yqq cron \
# Dagster
    && pip install -U --no-cache-dir \
        pip \
        setuptools \
        wheel \
        dagster==${DAGSTER_VERSION} \
        dagster-postgres==${DAGSTER_VERSION} \
        dagster-celery[flower,redis,kubernetes]==${DAGSTER_VERSION} \
        dagster-aws==${DAGSTER_VERSION} \
        dagster-k8s==${DAGSTER_VERSION} \
        dagster-celery-k8s==${DAGSTER_VERSION} \
# Cleanup
# "| :" forces a success signal even if some cleanup fails
    &&  rm -rf /var | : \
    &&  rm -rf /root/.cache  \
    &&  rm -rf /usr/lib/python2.7 \
    &&  rm -rf /usr/lib/x86_64-linux-gnu/guile

# ==> Add user code layer
WORKDIR /usr/src/app

# Copy our python package (wheel file, output of `poetry build`) and install it
COPY --from=build /usr/src/app/dist repo_package
COPY --from=build /usr/src/app/package_name package_name
RUN pip install --no-cache-dir repo_package/$(cat package_name)

# Defines dagster repo(s)
COPY workspace.yaml workspace.yaml

# Default Job Configs
COPY job_configs job_configs
