import json

from queue_listener import poll_once


def test_poll_once(aws_setup, test_file):
    """
    Given a docx file in an S3 bucket, and a message in a SQS queue referring to that s3 record
    When poll_once is called with the S3 client, SQS client, and queue URL
    Then it should:
        - take the message off the SQS queue,
        - fetch the DOCX and convert it to PDF with `libreoffice` via a subprocess
        - finally upload the PDF back to the same S3 bucket
    """
    s3_client, sqs_client, queue_url = aws_setup

    # 1. Put test DOCX in S3
    with open(test_file, "rb") as f:
        docx_content = f.read()
        s3_client.put_object(Bucket="test-bucket", Key="judgment.docx", Body=docx_content)

    # 2. Put message on queue
    message_body = json.dumps(
        {
            "Records": [
                {"s3": {"bucket": {"name": "test-bucket"}, "object": {"key": "judgment.docx", "eTag": '"abc123"'}}}
            ]
        }
    )
    sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)

    poll_once(s3_client, sqs_client, queue_url)

    # 4. Verify the results
    # Check PDF exists in S3
    pdf_response = s3_client.head_object(Bucket="test-bucket", Key="judgment.pdf")

    # Verify metadata
    assert pdf_response["Metadata"]["pdfsource"] == "pdf-conversion-libreoffice"

    # Verify message was removed from queue
    queue_attrs = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"])
    assert queue_attrs["Attributes"]["ApproximateNumberOfMessages"] == "0"

    # Optional: Verify PDF content if needed
    pdf_obj = s3_client.get_object(Bucket="test-bucket", Key="judgment.pdf")
    assert pdf_obj["ContentLength"] > 0
    assert pdf_obj["ContentType"] == "application/pdf"
