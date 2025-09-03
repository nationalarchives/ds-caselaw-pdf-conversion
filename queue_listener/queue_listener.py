import json
import os
import subprocess

import boto3
import botocore
import dotenv
import rollbar

import sys


def eprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def would_replace_custom_pdf(s3_client, bucket_name, upload_key):
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


def transform_docx(docx_filename, pdf_filename):
    """Run libreoffice to generate a pdf from a docx"""
    eprint(subprocess.run(f"soffice --convert-to pdf {docx_filename} --outdir /tmp".split(" "), timeout=30))

    # assert that there is now a file /tmp/pdf_filename
    if not os.path.exists(pdf_filename):
        raise RuntimeError(f"No pdf found at {pdf_filename}")

    # unlink the metadata for the PDF and linearize to remove it
    # both write back to pdf_filename
    subprocess.run(["exiftool", "-all:all=", pdf_filename], timeout=10)
    subprocess.run(["qpdf", "--linearize", "--replace-input", pdf_filename], timeout=10)


def handle_message(s3_client, sqs_client, queue_url, message):
    eprint(message)

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

        if would_replace_custom_pdf(s3_client, bucket_name, upload_key):
            rollbar_message = f"existing '{upload_key}' is from custom-pdfs, pdf-conversion is not overwriting it"
            rollbar.report_message(rollbar_message, "warning")
            eprint(rollbar_message)
            continue

        eprint(f"Downloading {download_key}")
        s3_client.download_file(Bucket=bucket_name, Key=download_key, Filename=docx_filename)
        transform_docx(docx_filename, pdf_filename)

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
            eprint(f"Uploaded {upload_key}")
        except FileNotFoundError as exception:
            eprint("LibreOffice probably didn't create a PDF for the input document.")
            rollbar.report_exc_info()
            eprint(exception)

        for file_to_delete in [pdf_filename, docx_filename]:
            try:
                os.remove(file_to_delete)
            except FileNotFoundError:
                pass

        eprint(f"Done with {upload_key}")

    # afterwards:
    sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])


def poll_once(s3_client, sqs_client, queue_url):
    eprint("Polling...")
    poll_time_seconds = 10
    messages_dict = sqs_client.receive_message(QueueUrl=queue_url, WaitTimeSeconds=poll_time_seconds)
    for message in messages_dict.get("Messages", []):
        handle_message(s3_client, sqs_client, queue_url, message)


def queue_listener():
    dotenv.load_dotenv()

    rollbar.init(
        os.getenv("ROLLBAR_ACCESS_TOKEN"),
        environment=os.getenv("ROLLBAR_ENV", default="unknown"),
    )

    # should be UNSET whenever using actual AWS
    # but set if we're using localstack
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
    )

    sqs_client = boto3.client(
        "sqs",
        endpoint_url=endpoint_url,
    )

    queue_url = os.getenv("QUEUE_URL")

    while True:
        poll_once(s3_client, sqs_client, queue_url)


if __name__ == "__main__":
    queue_listener()
