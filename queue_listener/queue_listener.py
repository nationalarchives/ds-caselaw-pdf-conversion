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
  sleep(1)
  print ("Polling")
  print (QUEUE_URL)
  for message in sqs_client.receive_message(QueueUrl=QUEUE_URL):
    print(message)
    message.delete()

print ("LISTENING")
exit()
for message in queue.receive_messages(MessageAttributeNames=['Author']):
    # Get the custom author message attribute if it was set
    author_text = ''
    if message.message_attributes is not None:
        author_name = message.message_attributes.get('Author').get('StringValue')
        if author_name:
            author_text = ' ({0})'.format(author_name)

    # Print out the body and author (if set)
    print('Hello, {0}!{1}'.format(message.body, author_text))

    # Let the queue know that the message is processed
    message.delete()
