
FROM python:3.12.2-slim


WORKDIR /code

# Install sudo
RUN apt-get update && apt-get install -y sudo && apt-get clean

# Create app_docker user and group and add to sudo group
RUN groupadd -r app_docker && \
    useradd -r -g app_docker -m app_docker && \
    usermod -aG sudo app_docker && \
    echo "app_docker ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set ownership of the code directory
RUN chown -R app_docker:app_docker /code

USER app_docker

COPY ./Pipfile /code/Pipfile
COPY ./Pipfile.lock /code/Pipfile.lock

# Install pipenv
RUN pip install --user --upgrade pip && \
    pip install --user pipenv

# Add .local/bin to PATH
ENV PATH="/home/app_docker/.local/bin:${PATH}"

# Install any needed packages specified in Pipfile
RUN pipenv install --deploy --ignore-pipfile

COPY ./app /code/app

# CMD ["tail", "-f", "/dev/null"]

CMD ["pipenv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]