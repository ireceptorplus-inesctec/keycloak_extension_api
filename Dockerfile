FROM python:3.9-alpine3.15

COPY requirements.txt /tmp/requirements.txt

RUN apk add --no-cache --virtual .build-deps gcc libc-dev \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apk del .build-deps gcc libc-dev

WORKDIR /app

COPY . /app


ENTRYPOINT [ "gunicorn" ]

CMD [ "--workers=4", "--bind=0.0.0.0:5000", "api:app" ]