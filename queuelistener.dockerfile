FROM python:3.12
COPY ./docker_context/poetry.lock .
COPY ./docker_context/pyproject.toml .
ENV PYTHONPATH=${PYTHONPATH}:${PWD} 
ENV PYTHONUNBUFFERED=1
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev


COPY ./queue_listener ./queue_listener
COPY ./docker_context .
# COPY ./fonts ./fonts

# # # Copy a LibreOffice config file which uses Times New Roman as the
# # # default font -- see README.txt
# # RUN mkdir -p /root/.config/libreoffice/4/user
# # RUN mkdir /root/.config/fontconfig
# # RUN cp registrymodifications.xcu /root/.config/libreoffice/4/user/registrymodifications.xcu
# # RUN cp fonts.conf /root/.config/fontconfig/fonts.conf

# # Install fonts
# RUN mkdir -p /usr/share/fonts/truetype/docker-context
# RUN find /fonts/ -name "*.ttf" -exec install -m644 {} /usr/share/fonts/truetype/docker-context/ \; || return 1
# RUN fc-cache -f && rm -rf /var/cache/*

ENV QUEUE_ARN=${QUEUE_ARN}
CMD ["python", "queue_listener/queue_listener.py"]