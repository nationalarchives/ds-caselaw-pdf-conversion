import boto3
import dotenv
import os
import json
from time import sleep

dotenv.load_dotenv()
QUEUE_URL=os.getenv("QUEUE_URL")
AWS_ENDPOINT_URL=os.getenv("AWS_ENDPOINT_URL")
AWS_REGION=os.getenv("AWS_REGION")
sqs_client = boto3.client('sqs', region_name = AWS_REGION, endpoint_url=AWS_ENDPOINT_URL)
s3_client = boto3.client('s3', region_name = AWS_REGION, endpoint_url=AWS_ENDPOINT_URL)

while True:
  print ("Polling")
  messages_dict = sqs_client.receive_message(QueueUrl=QUEUE_URL, WaitTimeSeconds=5)
  print(messages_dict)
  for message in messages_dict.get('Messages', []):
    json_body=json.loads(message['Body'])
    for record in json_body['Records']:
      bucket_name = record['s3']['bucket']['name'] # or ['arn']
      key = record['s3']['object']['key']
      s3_client.download_file(Bucket=bucket_name, Key=key, Filename="some.docx")
    #
    #
    #
    sqs_client.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle= message['ReceiptHandle'])

# libreoffice    | {'Messages': [
#   {'MessageId': '0f7c064e-79cc-45fe-b665-e8dcae6e5ade',
#    'ReceiptHandle': 'YzVkMDZiODQtYzRjOS00YjUxLThkZDktOTk2NDlhMDE5MDI3IGFybjphd3M6c3FzOnVzLWVhc3Qt
#    MTowMDAwMDAwMDAwMDA6cGRmLWNvbnZlcnNpb24tcXVldWUgMGY3YzA2NGUtNzljYy00NWZlLWI2NjUtZThkY2FlNmU1YWRl
#    IDE2NTQ2MDc3NjkuNTMyMDQ4',
#    'MD5OfBody': '4e37cbf470ab25034a88ce3cd0b03d5e',

#    'Body': '{"Records": [
#      {"eventVersion": "2.1", "eventSource": "aws:s3", "awsRegion": "us-east-1", "eventTime": "2022-06-07T13:13:48.335Z",
#      "eventName": "ObjectCreated:Put", "userIdentity": {"principalId": "AIDAJDPLRKLG7UEXAMPLE"}, "requestParameters":
#      {"sourceIPAddress": "127.0.0.1"}, "responseElements": {"x-amz-request-id": "a6badf1a", "x-amz-id-2":
#      "eftixk72aD6Ap51TnqcoF8eFidJG9Z/2"}, "s3": {"s3SchemaVersion": "1.0", "configurationId": "testConfigRule", "bucket":
#      {"name": "private-asset-bucket", "ownerIdentity": {"principalId": "A3NL1KOZZKExample"},
#      "arn": "arn:aws:s3:::private-asset-bucket"}, "object":
#      {"key": "judgment.docx", "size": 59709, "eTag": "\\"231cd8a7fbd165f135e304ff1c4bf230\\"", "versionId":
#      null, "sequencer": "0055AED6DCD90281E5"}}}]}'}], 'ResponseMetadata':
#        {'RequestId': '0SKXZOJCVTOE4K2W4GO158Q50JWFNW6YT535MDRTMZVCG68DMLY7', 'HTTPStatusCode': 200, 'HTTPHeaders':
#          {'content-type': 'text/xml', 'content-length': '1867', 'access-control-allow-origin': '*',
#           'access-control-allow-methods': 'HEAD,GET,PUT,POST,DELETE,OPTIONS,PATCH', 'access-control-allow-headers': 'authorization,cache-control,content-length,content-md5,content-type,etag,location,x-amz-acl,x-amz-content-sha256,x-amz-date,x-amz-request-id,x-amz-security-token,x-amz-tagging,x-amz-target,x-amz-user-agent,x-amz-version-id,x-amzn-requestid,x-localstack-target,amz-sdk-invocation-id,amz-sdk-request', 'access-control-expose-headers': 'etag,x-amz-version-id', 'connection': 'close', 'date': 'Tue, 07 Jun 2022 13:16:09 GMT', 'server': 'hypercorn-h11'}, 'RetryAttempts': 0}}
