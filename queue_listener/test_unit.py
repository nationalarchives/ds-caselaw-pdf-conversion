import os
import boto3
import pytest
from moto import mock_aws
from botocore.exceptions import ClientError
import json
import os
from unittest.mock import patch

from queue_listener import handle_message, poll_once, queue_listener, should_skip_file, would_replace_custom_pdf


@mock_aws
class TestWouldReplaceCustomPdf:
    """Test the would_replace_custom_pdf function"""

    def test_when_pdf_is_custom_then_returns_true(self):
        """
        Given a bucket and key corresponding to a PDF with "pdfsource": "custom-pdfs" in metadata
        When would_replace_custom_pdf is called
        Then it should return True
        """
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")

        # Setup test file with custom-pdfs metadata
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test.pdf",
            Body=b"test content",
            Metadata={"pdfsource": "custom-pdfs"},
        )

        assert would_replace_custom_pdf(s3_client, "test-bucket", "test.pdf")

    def test_when_pdf_has_different_metadata_then_returns_false(self):
        """
        Given a bucket and key corresponding to a PDF without "pdfsource": "custom-pdfs" in metadata
        When would_replace_custom_pdf is called
        Then it should return False
        """
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")

        s3_client.put_object(
            Bucket="test-bucket",
            Key="test.pdf",
            Body=b"test content",
            Metadata={"pdfsource": "kitten"},
        )

        assert not would_replace_custom_pdf(s3_client, "test-bucket", "test.pdf")

    def test_when_pdf_has_no_metadata_then_returns_false(self):
        """
        Given a bucket and key corresponding to a PDF with no metadata
        When would_replace_custom_pdf is called
        Then it should return False
        """
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")

        # Setup test file with no metadata
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test.pdf",
            Body=b"test content",
        )

        assert not would_replace_custom_pdf(s3_client, "test-bucket", "test.pdf")

    def test_when_pdf_not_found_then_returns_false(self):
        """
        Given a bucket that exists but key which does not
        When would_replace_custom_pdf is called
        Then it should return False
        """
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")

        assert not would_replace_custom_pdf(s3_client, "test-bucket", "nonexistent.pdf")

    def test_when_unexpected_error_then_raises(self):
        """
        Given a bucket name where the bucket does not exist
        When we call would_replace_custom_pdf
        Then it should raise a ClientError
        """
        s3_client = boto3.client("s3")
        with pytest.raises(ClientError):
            would_replace_custom_pdf(s3_client, "test-bucket", "test.pdf")


@mock_aws
class TestShouldSkipFile:
    """Test the should_skip_file function"""

    def test_when_file_has_no_tags_then_returns_true(self):
        """
        Given a docx file with no tags
        When should_skip_file is called
        Then it should return True (skip - waiting for cleansing)
        """
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")
        s3_client.put_object(Bucket="test-bucket", Key="test.docx", Body=b"test content")

        assert should_skip_file(s3_client, "test-bucket", "test.docx")

    def test_when_file_has_document_processor_version_then_returns_false(self):
        """
        Given a docx file with DOCUMENT_PROCESSOR_VERSION tag
        When should_skip_file is called
        Then it should return False (process - file is cleaned)
        """
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")
        s3_client.put_object(Bucket="test-bucket", Key="test.docx", Body=b"test content")

        # Tag with document processor version (cleaned)
        s3_client.put_object_tagging(
            Bucket="test-bucket",
            Key="test.docx",
            Tagging={"TagSet": [{"Key": "DOCUMENT_PROCESSOR_VERSION", "Value": "1.0.0"}]},
        )

        assert not should_skip_file(s3_client, "test-bucket", "test.docx")

    def test_when_file_missing_document_processor_version_then_returns_true(self):
        """
        Given a docx file without DOCUMENT_PROCESSOR_VERSION tag
        When should_skip_file is called
        Then it should return True (skip - not cleaned yet)
        """
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")
        s3_client.put_object(Bucket="test-bucket", Key="test.docx", Body=b"test content")

        # Tag with some other tag but not document processor version
        s3_client.put_object_tagging(
            Bucket="test-bucket",
            Key="test.docx",
            Tagging={"TagSet": [{"Key": "OTHER_TAG", "Value": "value"}]},
        )

        assert should_skip_file(s3_client, "test-bucket", "test.docx")

    def test_when_file_not_found_then_returns_true(self):
        """
        Given a file that does not exist
        When should_skip_file is called
        Then it should return True (skip to be safe)
        """
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")

        assert should_skip_file(s3_client, "test-bucket", "nonexistent.docx")


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


class TestHandleMessage:
    def test_handle_message_successful_conversion(self, test_file, aws_setup):
        s3_client, sqs_client, queue_url = aws_setup

        # Upload test document to S3 with DOCUMENT_PROCESSOR_VERSION tag (cleaned file)
        s3_client.put_object(Bucket="test-bucket", Key="test-document.docx", Body="test content")
        s3_client.put_object_tagging(
            Bucket="test-bucket",
            Key="test-document.docx",
            Tagging={"TagSet": [{"Key": "DOCUMENT_PROCESSOR_VERSION", "Value": "2.0.0"}]},
        )

        # Create and send message to SQS
        message_body = json.dumps(
            {
                "Records": [
                    {
                        "s3": {
                            "bucket": {"name": "test-bucket"},
                            "object": {"key": "test-document.docx", "eTag": '"abc123"'},
                        }
                    }
                ]
            }
        )

        sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)

        # Receive message to get valid receipt handle
        response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
        message = response["Messages"][0]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            # Create a mock PDF file that LibreOffice would create
            with open(f"/tmp/abc123.pdf", "w") as f:
                f.write("mock pdf content")

            handle_message(s3_client, sqs_client, queue_url, message)

        # Verify PDF was uploaded with correct metadata
        response = s3_client.head_object(Bucket="test-bucket", Key="test-document.pdf")
        assert response["Metadata"]["pdfsource"] == "pdf-conversion-libreoffice"

    def test_handle_message_skips_uncleaned_file(self, aws_setup):
        """Test that files without DOCUMENT_PROCESSOR_VERSION tag are skipped"""
        s3_client, sqs_client, queue_url = aws_setup

        # Upload test document WITHOUT DOCUMENT_PROCESSOR_VERSION tag (not cleaned yet)
        s3_client.put_object(Bucket="test-bucket", Key="test-document.docx", Body="test content")

        # Create and send message to SQS
        message_body = json.dumps(
            {
                "Records": [
                    {
                        "s3": {
                            "bucket": {"name": "test-bucket"},
                            "object": {"key": "test-document.docx", "eTag": '"abc123"'},
                        }
                    }
                ]
            }
        )

        sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)

        # Receive message to get valid receipt handle
        response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
        message = response["Messages"][0]

        with patch("subprocess.run") as mock_run:
            handle_message(s3_client, sqs_client, queue_url, message)
            # subprocess should not be called since file should be skipped
            mock_run.assert_not_called()

        # Verify PDF was NOT created
        with pytest.raises(ClientError) as exc_info:
            s3_client.head_object(Bucket="test-bucket", Key="test-document.pdf")
        assert exc_info.value.response["Error"]["Code"] == "404"

    def test_handle_message_with_existing_custom_pdf(self, aws_setup):
        s3_client, sqs_client, queue_url = aws_setup

        # Create docx with proper tags (cleaned, not converted)
        s3_client.put_object(Bucket="test-bucket", Key="test-document.docx", Body="test content")
        s3_client.put_object_tagging(
            Bucket="test-bucket",
            Key="test-document.docx",
            Tagging={"TagSet": [{"Key": "DOCUMENT_PROCESSOR_VERSION", "Value": "2.0.0"}]},
        )

        # Create existing custom PDF
        s3_client.put_object(
            Bucket="test-bucket", Key="test-document.pdf", Body="existing pdf", Metadata={"pdfsource": "custom-pdfs"}
        )

        # Create and send message to SQS
        message_body = json.dumps(
            {
                "Records": [
                    {
                        "s3": {
                            "bucket": {"name": "test-bucket"},
                            "object": {"key": "test-document.docx", "eTag": '"abc123"'},
                        }
                    }
                ]
            }
        )

        sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)

        # Receive message to get valid receipt handle
        response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
        message = response["Messages"][0]

        with patch("rollbar.report_message") as mock_rollbar:
            handle_message(s3_client, sqs_client, queue_url, message)
            mock_rollbar.assert_called_once()


def test_poll_once_with_messages(aws_setup):
    s3_client, sqs_client, queue_url = aws_setup

    # Add message to queue
    message_body = json.dumps(
        {
            "Records": [
                {"s3": {"bucket": {"name": "test-bucket"}, "object": {"key": "test-document.docx", "eTag": '"abc123"'}}}
            ]
        }
    )

    sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)

    with patch("queue_listener.handle_message") as mock_handle:
        poll_once(s3_client, sqs_client, queue_url)
        mock_handle.assert_called_once()
        mock_handle.call_args[0][0] == s3_client
        mock_handle.call_args[0][1] == sqs_client
        mock_handle.call_args[0][2] == queue_url
        mock_handle.call_args[0][3]["Body"] == message_body
