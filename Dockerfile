FROM ubuntu:20.04

RUN apt-get update -y && \
    apt-get install -y build-essential python3-pip python3-dev

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 5000

ENTRYPOINT [ "gunicorn" ]

CMD [ "--workers=4", "--bind=0.0.0.0:8000", "api:app" ]