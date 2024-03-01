FROM python:3.11.3-alpine3.18

ENV PYTHONUNBUFFERED 1

WORKDIR /app
#COPY requirements.txt /app/
#RUN python -m venv venv
#RUN source /app/venv/bin/activate
#RUN pip install --upgrade pip && \
#    pip install -r /app/requirements.txt


COPY . /app
#ENTRYPOINT python main.py