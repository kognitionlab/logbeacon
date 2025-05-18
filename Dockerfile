FROM python:3.10.17-alpine3.21

ENV PORT 5000

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    build-base

WORKDIR /app

COPY ./src/ /app/src/
COPY ./main.py /app/main.py

ENTRYPOINT ["python", "main.py"]

CMD ["--backend", "docker", "--port", $PORT]