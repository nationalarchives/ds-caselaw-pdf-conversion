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

COPY ./docker_context/poetry.lock .
COPY ./docker_context/pyproject.toml .
RUN pip install poetry==1.1.11
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY ./queue_listener ./queue_listener
COPY ./docker_context .
COPY ./fonts /root/fonts

# Copy a LibreOffice config file which uses Times New Roman as the
# default font -- see README.txt
RUN mkdir -p /root/.config/libreoffice/4/user
RUN mkdir /root/.config/fontconfig
RUN cp registrymodifications.xcu /root/.config/libreoffice/4/user/registrymodifications.xcu
RUN cp fonts.conf /root/.config/fontconfig/fonts.conf

RUN apk --no-cache add font-croscore && \
    update-ms-fonts && \
    fc-cache -f

# Google fonts
RUN wget https://github.com/google/fonts/archive/main.tar.gz -O gf.tar.gz
RUN tar -xf gf.tar.gz
RUN mkdir -p /usr/share/fonts/truetype/google-fonts
RUN find /fonts-main/ -name "*.ttf" -exec install -m644 {} /usr/share/fonts/truetype/google-fonts/ \; || return 1
RUN find /root/fonts/ -name "*.ttf" -exec install -m644 {} /usr/share/fonts/truetype/google-fonts/ \; || return 1
RUN rm -f gf.tar.gz
RUN fc-cache -f && rm -rf /var/cache/*

ENV QUEUE_ARN=${QUEUE_ARN}
CMD ["python", "queue_listener/queue_listener.py"]
