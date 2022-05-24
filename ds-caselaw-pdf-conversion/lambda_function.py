import os
import subprocess
import tarfile
from io import BytesIO

import boto3

libre_office_install_dir = "/tmp/instdir"

# open file
file = tarfile.open("/opt/lo.tar.gz")
# extracting file
file.extractall(libre_office_install_dir)
file.close()


def load_libre_office():
    # if os.path.exists(libre_office_install_dir) and os.path.isdir(libre_office_install_dir):
    #     print('We have a cached copy of LibreOffice, skipping extraction')
    # else:
    #     print('No cached copy of LibreOffice, extracting tar stream from Brotli file.')
    #     buffer = BytesIO()
    #
    # print('Extracting tar stream to /tmp for caching.')
    # with tarfile.open(fileobj=buffer) as tar:
    #     tar.extractall('/tmp')
    # print('Done caching LibreOffice!')
    subprocess.run([f"{libre_office_install_dir}/program/soffice.bin", "--help"])
    return f"{libre_office_install_dir}/program/soffice.bin"


def handler(event, context):
    print("In Lambda")
    load_libre_office()
