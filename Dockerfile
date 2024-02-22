FROM python:3.11.3-alpine3.18

ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt


COPY . /app
ENTRYPOINT python main.py