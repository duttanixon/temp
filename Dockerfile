
FROM python:3.12.2-slim


WORKDIR /code


COPY ./Pipfile /code/Pipfile
COPY ./Pipfile.lock /code/Pipfile.lock

# Install pipenv
RUN pip install --upgrade pip && \
    pip install pipenv

# Install any needed packages specified in Pipfile
RUN pipenv install --deploy --ignore-pipfile

# Create app_docker user and group
RUN groupadd -r app_docker && \
    useradd -r -g app_docker app_docker && \
    mkdir -p /data && \
    chown -R app_docker:app_docker /data

COPY ./app /code/app


CMD ["pipenv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]