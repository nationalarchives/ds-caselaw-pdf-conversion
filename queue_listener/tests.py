from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

import queue_listener


# TRUTHY
@patch(
    "queue_listener.s3_client.head_object",
    return_value={
        "ResponseMetadata": {"HTTPHeaders": {"x-amz-meta-pdfsource": "custom-pdfs"}}
    },
)
def test_would_replace_is_custom(head_object):
    """There is a pdfsource, but it is custom-pdfs"""
    assert queue_listener.would_replace_custom_pdf("", "")
    head_object.assert_called_once()


# FALSEY
@patch(
    "queue_listener.s3_client.head_object",
    return_value={
        "ResponseMetadata": {"HTTPHeaders": {"x-amz-meta-pdfsource": "kitten"}}
    },
)
def test_would_replace_not_custom(head_object):
    """There is a pdfsource, but it isn't custom-pdfs"""
    assert not queue_listener.would_replace_custom_pdf("", "")
    head_object.assert_called_once()


@patch("queue_listener.s3_client.head_object", return_value={})
def test_would_replace_is_empty(head_object):
    """There is a file, but no pdfsource header at all"""
    assert not queue_listener.would_replace_custom_pdf("", "")
    head_object.assert_called_once()


@patch(
    "queue_listener.s3_client.head_object",
    side_effect=ClientError(
        error_response={"Error": {"Message": "Not Found"}}, operation_name=""
    ),
)
def test_would_replace_is_not_found(head_object):
    """There is no such file, so there's nothing to be worried about overwriting"""
    assert not queue_listener.would_replace_custom_pdf("", "")
    head_object.assert_called_once()


# ERRORY
@patch(
    "queue_listener.s3_client.head_object",
    side_effect=ClientError(
        error_response={"Error": {"Message": "Out Of Cheese"}}, operation_name=""
    ),
)
def test_would_replace_is_bad_response(head_object):
    """An unexpected error occurred, so we re-raise"""
    with pytest.raises(ClientError):
        queue_listener.would_replace_custom_pdf("", "")
    head_object.assert_called_once()
