FROM lscr.io/linuxserver/libreoffice:7.2.2.2-r2-ls36 as libreoffice_base
RUN apk --no-cache add msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f
RUN apk add libffi libffi-dev build-base gcc python3-dev curl

# Install python/pip
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools wheel

COPY ./docker_context/poetry.lock .
COPY ./docker_context/pyproject.toml .
RUN pip3 install poetry==1.4.2
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

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
