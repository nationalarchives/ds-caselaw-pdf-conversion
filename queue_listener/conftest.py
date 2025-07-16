import os
from moto import mock_aws
import boto3
import pytest


@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def aws_setup():
    with mock_aws():
        # Set up S3
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket="test-bucket")

        # Set up SQS
        sqs = boto3.client("sqs")
        queue_url = sqs.create_queue(QueueName="test-queue")["QueueUrl"]

        yield s3, sqs, queue_url


@pytest.fixture
def test_file(tmp_path):
    """Create a test DOCX file."""
    file_path = tmp_path / "test.docx"
    file_path.write_text("test content")
    return str(file_path)
