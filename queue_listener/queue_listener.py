import json
import os
import subprocess

import boto3
import dotenv

dotenv.load_dotenv()
QUEUE_URL = os.getenv("QUEUE_URL")
# AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
# AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
AWS_REGION = os.getenv("AWS_REGION")
POLL_SECONDS = 10
sqs_client = boto3.client(
    "sqs", region_name=AWS_REGION
)  # set endpoint_url=AWS_ENDPOINT_URL on localstack
s3_client = boto3.client("s3", region_name=AWS_REGION)

while True:
    print("Polling")
    messages_dict = sqs_client.receive_message(
        QueueUrl=QUEUE_URL, WaitTimeSeconds=POLL_SECONDS
    )
    for message in messages_dict.get("Messages", []):
        print(message)
        json_body = json.loads(message["Body"])
        for record in json_body.get("Records", []):
            bucket_name = record["s3"]["bucket"]["name"]  # or ['arn']
            download_key = record["s3"]["object"]["key"]
            etag = record["s3"]["object"]["eTag"].replace('"', "")
            docx_filename = f"/tmp/{etag}.docx"
            pdf_filename = f"/tmp/{etag}.pdf"

            print(f"Downloading {download_key}")
            s3_client.download_file(
                Bucket=bucket_name, Key=download_key, Filename=docx_filename
            )

            print(
                subprocess.run(
                    f"soffice --convert-to pdf {docx_filename} --outdir /tmp".split(" ")
                )
            )

            # split on dots, remove last part and recombine with dots again
            # to have net effect of removing extension
            key_no_extension = ".".join(download_key.split(".")[:-1])
            upload_key = key_no_extension + ".pdf"

            # NOTE: there's a risk that some.pdf doesn't exist, we need to handle that case.
            try:
                s3_client.upload_file(
                    Bucket=bucket_name, Key=upload_key, Filename=pdf_filename
                )
                print(f"Uploaded {upload_key}")
            except FileNotFoundError as exception:
                print("LibreOffice probably didn't create a PDF for the input document.")
                print(exception)

            for file_to_delete in [pdf_filename, docx_filename]:
                try:
                    os.remove(file_to_delete)
                except FileNotFoundError:
                    pass

        # afterwards:
        sqs_client.delete_message(
            QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"]
        )
