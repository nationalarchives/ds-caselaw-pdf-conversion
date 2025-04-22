FROM lscr.io/linuxserver/libreoffice:7.6.7@sha256:6e74fc895f5f603dbc91f05fd2af7a924c162d604e653dc58d9d81fb3fa14c88 AS libreoffice_base
RUN apk --no-cache add msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f
RUN apk add libffi libffi-dev build-base gcc python3-dev curl

# Install python/poetry
ENV PYTHONUNBUFFERED=1
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -
COPY ./docker_context/poetry.lock .
COPY ./docker_context/pyproject.toml .
RUN /etc/poetry/bin/poetry config virtualenvs.create false \
  && /etc/poetry/bin/poetry install --no-interaction --no-ansi

COPY ./queue_listener ./queue_listener
COPY ./docker_context .
COPY ./fonts ./fonts

ENV HOME=/

# Copy a LibreOffice config file which uses Times New Roman as the
# default font -- see README.txt
RUN mkdir -p $HOME/.config/libreoffice/4/user
RUN mkdir $HOME/.config/fontconfig
RUN cp registrymodifications.xcu $HOME/.config/libreoffice/4/user/registrymodifications.xcu
RUN cp fonts.conf $HOME/.config/fontconfig/fonts.conf

# Install fonts
RUN mkdir -p /usr/share/fonts/truetype/docker-context
RUN find /fonts/ -name "*.ttf" -exec install -m644 {} /usr/share/fonts/truetype/docker-context/ \; || return 1
RUN fc-cache -f && rm -rf /var/cache/*

ENV QUEUE_ARN=${QUEUE_ARN}
CMD ["python", "queue_listener/queue_listener.py"]
