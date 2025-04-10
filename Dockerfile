
FROM python:3.12.2-slim


WORKDIR /code


COPY ./Pipfile /code/Pipfile
COPY ./Pipfile.lock /code/Pipfile.lock

# Install pipenv
RUN pip install --upgrade pip && \
    pip install pipenv

# Install any needed packages specified in Pipfile
RUN pipenv install --deploy --ignore-pipfile


COPY ./app /code/app


CMD ["fastapi", "run", "app/main.py", "--port", "80"]