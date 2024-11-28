FROM python:3.11

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && poetry install --no-root

COPY . .

EXPOSE 8080

CMD ["poetry", "run", "python", "-u", "server.py"]
