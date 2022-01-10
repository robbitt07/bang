FROM python:3.7.4

RUN apt-get update -qq && apt-get install -y -qq \
    # std libs
    git less nano curl \
    ca-certificates \
    wget build-essential\
    # postgresql
    libpq-dev postgresql-client && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

## Upgrading pip
RUN pip install --upgrade pip

# Make directory for code repository and declare as base working directory
WORKDIR /app

# Move requirements file and install requirements
COPY requirements/requirements.txt ./
COPY requirements/deploy_requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r deploy_requirements.txt

# Copy all source code (no need to create volume)
COPY ./bang ./

# Collect static (only used for local file serving)
RUN ["python", "manage.py", "collectstatic", "--no-input"]
RUN ["python", "manage.py", "migrate"]
RUN ["python", "build/build.py"]
RUN ["python", "initialize_scheduler.py"]

EXPOSE 8000

CMD exec gunicorn bang.wsgi:application --bind 0.0.0.0:8000 --workers 3