FROM python:3.9-alpine3.13
LABEL maintainer="Balu"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./ /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp &&\
    adduser \
        --disabled-password \
        --no-create-home \
        fast-user

ENV PATH="/py/bin:$PATH"

USER fast-user
