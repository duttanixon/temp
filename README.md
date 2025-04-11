# cc-platform-backend-90012


## Tech Stack

- Python 3.12
- FastAPI


## Local Development

### Prerequisites

- Python 3.12+
- Pipenv

### Setup

<details>
<summary>Python Environment Setup</summary>

```bash
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
. "$HOME/.asdf/asdf.sh"
. "$HOME/.asdf/completions/asdf.bash"
source ~/.bashrc
asdf plugin list all | grep -e python
asdf plugin add python
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev libpq-dev python3-dev
asdf install python 3.12.2
asdf global python 3.12.2
asdf current python
```

- Confirm the python version is 3.12.2
```bash
python3 --version
```
</details>

<details>
<summary>Pipenv Installation</summary>

For Linux:
```bash
python3 -m pip install --user pipenv
```
> **Note**: Make sure to export the install path to .bashrc file 

For mac:
```bash
brew install pipenv
```
</details>

<details>
<summary>Running the Application</summary>

```bash
pipenv sync --dev
pipenv run uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000
</details>