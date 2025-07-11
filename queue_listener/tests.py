import os
import boto3
import pytest
from moto import mock_aws
from botocore.exceptions import ClientError

import queue_listener


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@mock_aws
class TestWouldReplaceCustomPdf:
    """Test the would_replace_custom_pdf function"""

    def test_when_pdf_is_custom_then_returns_true(self):
        """
        Given a bucket and key corresponding to a PDF with "pdfsource": "custom-pdfs" in metadata
        When would_replace_custom_pdf is called
        Then it should return True
        """
        s3_client = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION"))

        # Create the bucket
        s3_client.create_bucket(
            Bucket="test-bucket",
        )

        # Setup test file with custom-pdfs metadata
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test.pdf",
            Body=b"test content",
            Metadata={"pdfsource": "custom-pdfs"},
        )

        assert queue_listener.would_replace_custom_pdf(s3_client, "test-bucket", "test.pdf")

    def test_when_pdf_has_different_metadata_then_returns_false(self):
        """
        Given a bucket and key corresponding to a PDF without "pdfsource": "custom-pdfs" in metadata
        When would_replace_custom_pdf is called
        Then it should return False
        """
        # Setup test file with different metadata
        s3_client = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION"))

        # Create the bucket
        s3_client.create_bucket(
            Bucket="test-bucket",
        )
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test.pdf",
            Body=b"test content",
            Metadata={"pdfsource": "kitten"},
        )

        assert not queue_listener.would_replace_custom_pdf(s3_client, "test-bucket", "test.pdf")

    def test_when_pdf_has_no_metadata_then_returns_false(self):
        """
        Given a bucket and key corresponding to a PDF with no metadata
        When would_replace_custom_pdf is called
        Then it should return False
        """
        s3_client = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION"))

        s3_client.create_bucket(
            Bucket="test-bucket",
        )

        # Setup test file with no metadata
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test.pdf",
            Body=b"test content",
        )

        assert not queue_listener.would_replace_custom_pdf(s3_client, "test-bucket", "test.pdf")

    def test_when_pdf_not_found_then_returns_false(self):
        """
        Given a bucket that exists but key which does not
        When would_replace_custom_pdf is called
        Then it should return False
        """
        s3_client = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION"))

        # Create the bucket
        s3_client.create_bucket(
            Bucket="test-bucket",
        )

        assert not queue_listener.would_replace_custom_pdf(s3_client, "test-bucket", "nonexistent.pdf")

    def test_when_unexpected_error_then_raises(self):
        """
        Given a bucket name where the bucket does not exist
        When we call would_replace_custom_pdf
        Then it should raise a ClientError
        """
        s3_client = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION"))
        with pytest.raises(ClientError):
            queue_listener.would_replace_custom_pdf(s3_client, "test-bucket", "test.pdf")
