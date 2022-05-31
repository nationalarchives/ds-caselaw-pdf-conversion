FROM lscr.io/linuxserver/libreoffice:latest as libreoffice_base
RUN apk --no-cache add msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f

#RUN apt install msttcorefonts ttf-mscorefonts-installer
