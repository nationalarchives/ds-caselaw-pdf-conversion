import subprocess
import tarfile
import glob
import boto3


def extract_libre_office():
    # open file
    file = tarfile.open("/opt/br-layer.tar.gz")
    # extract file
    file.extractall('/tmp')
    file.close()
    return "/tmp/instdir"

def libre_office_executable():
    libre_office_install_dir = extract_libre_office()
    return f"{libre_office_install_dir}/program/soffice.bin"

def handler(event, context):
    lo = libre_office_executable()
    output = subprocess.run([lo, "--help"], capture_output=True, text=True)
    print("stdout:")
    print(output.stdout)
    print("stderr:")
    print(output.stderr)
