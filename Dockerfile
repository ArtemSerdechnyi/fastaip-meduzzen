FROM python:3.12-alpine3.19
LABEL authors="artem"

ARG PORT
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ADD .env.docker /code/.env

EXPOSE ${PORT}

COPY ./app ./app
