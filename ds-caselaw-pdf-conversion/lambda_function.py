import subprocess
import tarfile
import os
import boto3
import urllib3
import glob

# def get_s3_client():
#     session = boto3.session.Session(
#         aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#         aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
#     )
#     print (session)
#     return session.client("s3", endpoint_url=os.getenv("AWS_ENDPOINT_URL"))

# def store_file(file, folder, filename, s3_client: Session.client):
#     pathname = f"{folder}/{filename}"
#     try:
#         s3_client.upload_fileobj(file, os.getenv("AWS_BUCKET_NAME"), pathname)
#         print(f"Upload Successful {pathname}")
#     except FileNotFoundError:
#         print(f"The file {pathname} was not found")
#     except NoCredentialsError:
#         print("Credentials not available")

def extract_libre_office():
    file = tarfile.open("/opt/br-layer.tar.gz")
    file.extractall("/tmp")
    file.close()
    return "/tmp/instdir"

def s3_urls(event):
    for record in event['Records']:
        region = record['awsRegion']
        bucket = record['s3']['bucket']['name']
        filename = record['s3']['object']['key']
        yield f"https://{bucket}.s3.{region}.amazonaws.com/{filename}"

def libre_office_executable():
    libre_office_install_dir = extract_libre_office()
    return f"{libre_office_install_dir}/program/soffice.bin"

def extract_fonts():
    os.makedirs('/tmp/instdir/share/fonts/truetype/', exist_ok=True)
    subprocess.call('cp fonts/times.ttf /tmp/instdir/share/fonts/truetype/times.ttf', shell=True)
    subprocess.call('cp fonts/fontconfig.conf /tmp/instdir/share/fonts/truetype/fontconfig.conf', shell=True)


def handler(event, context):
    # client = get_s3_client()
    extract_fonts()
    lo = libre_office_executable()

    # Retrieve docx file from S3
    for s3_url in s3_urls(event):
        print(s3_url)
        http = urllib3.PoolManager()
        try:
            file = http.request("GET", s3_url)
        except Exception as e:
            # Maybe some handling later
            raise

        # Store it in the /tmp directory
        with open('/tmp/judgment.docx', "wb") as out:
            out.write(file.data)

        print (file.data[:4]) # should be PK


    my_env = os.environ.copy()
    print ("cwd", os.getcwd())
    user = os.path.expanduser('~')
    os.mkdir(user)
    my_env['FONTCONFIG_FILE'] = "/tmp/instdir/share/fonts/truetype/fontconfig.conf"
    my_env["FONTCONFIG_PATH"] = "/tmp/instdir/share/fonts/truetype"

    my_env["PATH"] = "/usr/sbin:/sbin:" + my_env["PATH"]
    command_string = f"{lo} --strace --headless --norestore --invisible --nodefault --nofirststartwizard --nolockcheck --nologo --convert-to pdf:writer_pdf_Export --outdir /tmp /tmp/judgment.docx"
    output = subprocess.run(command_string.split(), capture_output=True, text=True, env=my_env)
    print(glob.glob("/tmp/instdir/**/gdbtrace.log"))
    print(glob.glob("/tmp/*.docx"))
    print(glob.glob("/tmp/*.pdf"))
    print("stdout:")
    print(output.stdout)
    print("stderr:")
    print(output.stderr)
    with open('/tmp/judgment.pdf', 'r') as f:
        print(f.read()[:4]) # PDF%
