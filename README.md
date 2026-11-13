# cloud-tasks


Веб-сервис управления задачами на Flask + SQLite в GitHub Codespaces

## Технологии

- Python

- Flask

- SQLite


## Структура

- app.py - сервер flask
- requirements.txt - зависимости
- .devcontainer/devcontainer.json - конфигурация Codespaces
- data/tasks.sqlite3 - база


## Запуск
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

python app.py
