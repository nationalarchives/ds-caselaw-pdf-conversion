FROM lscr.io/linuxserver/libreoffice:latest as libreoffice_base
RUN apk --no-cache add msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f
RUN apk add libffi libffi-dev build-base gcc python3-dev curl

# Install python/pip
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools wheel

COPY ./docker_context .
RUN pip install poetry==1.1.11
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY ./queue_listener ./queue_listener

ENV QUEUE_ARN=${QUEUE_ARN}
CMD ["python", "queue_listener/queue_listener.py"]
