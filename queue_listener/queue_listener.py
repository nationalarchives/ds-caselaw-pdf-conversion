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


def should_skip_file(s3_client, bucket_name, object_key):
    """
    Check if the docx file should be skipped by checking its tags.
    Returns True if the file should be skipped, False if it should be processed.

    Skips if:
    - File hasn't been cleaned yet (no DOCUMENT_PROCESSOR_VERSION tag) - waiting for cleansing

    Note: We check for the presence of DOCUMENT_PROCESSOR_VERSION but not its value.
    Any version indicates the file has been cleaned. This allows PDFs to be automatically
    regenerated when files are re-cleaned with a newer version of the document processor.
    """
    try:
        # Get object tags
        tags_response = s3_client.get_object_tagging(Bucket=bucket_name, Key=object_key)
        tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("TagSet", [])}

        # Check: Has the file been cleaned by the document processor?
        if "DOCUMENT_PROCESSOR_VERSION" not in tags:
            eprint(
                f"File {object_key} has not been cleaned yet (no DOCUMENT_PROCESSOR_VERSION tag). "
                f"Skipping until cleansing process completes."
            )
            return True

        # File is cleaned - proceed with processing
        return False

    except botocore.exceptions.ClientError as exception:
        # If we can't get tags, skip processing to be safe (don't process uncleaned files)
        if exception.response["Error"]["Code"] == "NoSuchTagSet":
            eprint(f"No tags found for {object_key}. Skipping (assuming not cleaned yet).")
            return True
        eprint(f"Error getting tags for {object_key}: {exception}. Skipping to be safe.")
        return True


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

        # Check if the docx file should be processed:
        # - Skip if not cleaned yet (no DOCUMENT_PROCESSOR_VERSION tag)
        if should_skip_file(s3_client, bucket_name, download_key):
            continue

        if would_replace_custom_pdf(s3_client, bucket_name, upload_key):
            rollbar_message = f"existing '{upload_key}' is from custom-pdfs, pdf-conversion is not overwriting it"
            rollbar.report_message(rollbar_message, "warning")
            eprint(rollbar_message)
            continue

        eprint(f"Downloading {download_key}")
        s3_client.download_file(Bucket=bucket_name, Key=download_key, Filename=docx_filename)

        # this could probably fail, we should do something about that

        eprint(subprocess.run(f"soffice --convert-to pdf {docx_filename} --outdir /tmp".split(" "), timeout=30))

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
