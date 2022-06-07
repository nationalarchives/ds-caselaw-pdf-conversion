import boto3
import dotenv
import os
from time import sleep

dotenv.load_dotenv()
QUEUE_URL=os.getenv("QUEUE_URL")
AWS_ENDPOINT_URL=os.getenv("AWS_ENDPOINT_URL")
print (AWS_ENDPOINT_URL)
sqs_client = boto3.client('sqs', region_name = 'us-east-1', endpoint_url=AWS_ENDPOINT_URL)

while True:
  print ("Polling")
  messages_dict = sqs_client.receive_message(QueueUrl=QUEUE_URL, WaitTimeSeconds=5)
  print (messages_dict)
  for message in messages_dict.get('Messages', []):
    print(message["Body"])
    sqs_client.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle= message['ReceiptHandle'])
