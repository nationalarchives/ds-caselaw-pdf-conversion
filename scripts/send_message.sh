source .env

awslocal sqs send-message --queue-url ${QUEUE_URL} --message-body "s3://private-asset-bucket/judgment.docx"
