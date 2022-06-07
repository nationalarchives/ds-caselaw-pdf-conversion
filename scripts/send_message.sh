source .env

awslocal sqs send-message --queue-url ${QUEUE_URL} --message-body "kitten"
