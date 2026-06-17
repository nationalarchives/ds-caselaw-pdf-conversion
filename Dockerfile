FROM lscr.io/linuxserver/libreoffice:25.8.1@sha256:e1436c3edbc1b95b740cce5306697e4945afc7b67fbd5e3896ddc7f1aae64434 AS libreoffice_base
RUN apk --no-cache add msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f
RUN apk add -u libffi libffi-dev build-base gcc python3-dev curl

# Install python/poetry
ENV PYTHONUNBUFFERED=1
RUN curl -sSL https://install.python-poetry.org -o /tmp/poetry-installer.py && \
    POETRY_HOME=/etc/poetry python3 /tmp/poetry-installer.py || \
    { cat /poetry-installer-error-*; exit 1; }
COPY ./docker_context/poetry.lock .
COPY ./docker_context/pyproject.toml .
RUN /etc/poetry/bin/poetry config virtualenvs.create false
RUN /etc/poetry/bin/poetry install --no-interaction --no-ansi


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

# Run as non-root user (linuxserver.io already creates user at 1000:1000)
USER 1000:1000

CMD ["python", "queue_listener/queue_listener.py"]
