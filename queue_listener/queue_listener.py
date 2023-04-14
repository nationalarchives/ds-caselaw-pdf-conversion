import json
import os
import subprocess

import boto3
import botocore
import dotenv
import rollbar

dotenv.load_dotenv()

rollbar.init(
    os.getenv("ROLLBAR_ACCESS_TOKEN"),
    environment=os.getenv("ROLLBAR_ENV", default="unknown"),
)
QUEUE_URL = os.getenv("QUEUE_URL")
# should be UNSET whenever using actual AWS
# but set if we're using localstack
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_REGION = os.getenv("AWS_REGION")
POLL_SECONDS = 10
sqs_client = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    endpoint_url=ENDPOINT_URL,
)
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    endpoint_url=ENDPOINT_URL,
)


def would_replace_custom_pdf(bucket_name, upload_key):
    """
    If a PDF file with the target name already exists, and has metadata of 'custom-pdfs',
    we should not overwrite the file with an automatically generated PDF.
    """

    # get the metadata from S3
    try:
        metadata = s3_client.head_object(Bucket=bucket_name, Key=upload_key)
    except botocore.exceptions.ClientError as exception:
        # we expect in most instances that the file won't exist, and that's OK
        if exception.response["Error"]["Message"] == "Not Found":
            metadata = {}
        else:
            raise

    # get the source of the document from the S3 metadata
    try:
        source = metadata["ResponseMetadata"]["HTTPHeaders"]["x-amz-meta-pdfsource"]
    except KeyError:
        source = None

    return source == "custom-pdfs"


def handle_message(message):
    print(message)
    json_body = json.loads(message["Body"])
    for record in json_body.get("Records", []):
        bucket_name = record["s3"]["bucket"]["name"]  # or ['arn']
        download_key = record["s3"]["object"]["key"]
        etag = record["s3"]["object"]["eTag"].replace('"', "")
        docx_filename = f"/tmp/{etag}.docx"
        pdf_filename = f"/tmp/{etag}.pdf"

        # split on dots, remove last part and recombine with dots again
        # to have net effect of removing extension
        key_no_extension = ".".join(download_key.split(".")[:-1])
        upload_key = key_no_extension + ".pdf"

        if would_replace_custom_pdf(bucket_name, upload_key):
            rollbar_message = f"existing '{upload_key}' is from custom-pdfs, pdf-conversion is not overwriting it"
            rollbar.report_message(rollbar_message, "warning")
            print(rollbar_message)
            continue

        print(f"Downloading {download_key}")
        s3_client.download_file(
            Bucket=bucket_name, Key=download_key, Filename=docx_filename
        )

        print(
            subprocess.run(
                f"soffice --convert-to pdf {docx_filename} --outdir /tmp".split(" ")
            )
        )

        # NOTE: there's a risk that the local pdf file doesn't exist, we need to handle that case.
        try:
            s3_client.upload_file(
                Bucket=bucket_name,
                Key=upload_key,
                Filename=pdf_filename,
                ExtraArgs={
                    "ContentType": "application/pdf",
                    "Metadata": {"pdfsource": "pdf-conversion-libreoffice"},
                },
            )
            print(f"Uploaded {upload_key}")
        except FileNotFoundError as exception:
            print("LibreOffice probably didn't create a PDF for the input document.")
            rollbar.report_exc_info()
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


def poll_once():
    print("Polling...")
    messages_dict = sqs_client.receive_message(
        QueueUrl=QUEUE_URL, WaitTimeSeconds=POLL_SECONDS
    )
    for message in messages_dict.get("Messages", []):
        handle_message(message)


if __name__ == "__main__":
    while True:
        poll_once()
