FROM lscr.io/linuxserver/libreoffice:latest as libreoffice_base
RUN apk --no-cache add msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f
RUN apk add libffi libffi-dev build-base gcc python3-dev curl

# Install python/poetry
ENV PYTHONUNBUFFERED=1
RUN curl -sSL https://install.python-poetry.org  | python3 -
COPY ./docker_context/poetry.lock .
COPY ./docker_context/pyproject.toml .
RUN /config/.local/bin/poetry config virtualenvs.create false \
  && /config/.local/bin/poetry install --no-interaction --no-ansi

COPY ./queue_listener ./queue_listener
COPY ./docker_context .
COPY ./fonts ./fonts

# Copy a LibreOffice config file which uses Times New Roman as the
# default font -- see README.txt
RUN mkdir -p /root/.config/libreoffice/4/user
RUN mkdir /root/.config/fontconfig
RUN cp registrymodifications.xcu /root/.config/libreoffice/4/user/registrymodifications.xcu
RUN cp fonts.conf /root/.config/fontconfig/fonts.conf

# Install fonts
RUN mkdir -p /usr/share/fonts/truetype/docker-context
RUN find /fonts/ -name "*.ttf" -exec install -m644 {} /usr/share/fonts/truetype/docker-context/ \; || return 1
RUN fc-cache -f && rm -rf /var/cache/*

ENV QUEUE_ARN=${QUEUE_ARN}
CMD ["python", "queue_listener/queue_listener.py"]
