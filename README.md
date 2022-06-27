Acquired /config/.config/libreoffice/4/user/registrymodifications.xcu from the original libreoffice docker container after changing
the default fonts in the Tools, Options, LibreOffice Writer, Basic Fonts (Western) to Noto Sans throughout, then used
cat orig_mods.xcu | sed 's/Noto Sans/Times New Roman/g' > modified_mods.xcu
and reupload
