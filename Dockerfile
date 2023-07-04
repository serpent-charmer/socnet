from python:3

RUN python3 -m pip install poetry
RUN mkdir /main

WORKDIR /main 
COPY pyproject.toml /main
RUN poetry install

COPY app /main/app
COPY db /main/db
COPY tests /main/tests
COPY alembic /main/alembic
COPY alembic.ini /main

CMD poetry run pytest && poetry run alembic upgrade head && poetry run uvicorn app:app --host 0.0.0.0 --port 80
