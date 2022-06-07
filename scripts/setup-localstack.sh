source .env

awslocal sqs create-queue --queue-name pdf-conversion-queue

awslocal s3api create-bucket \
  --bucket private-asset-bucket

awslocal --endpoint-url=http://localhost:4566 \
s3api put-bucket-notification-configuration --bucket private-asset-bucket \
--notification-configuration file://aws-config/s3-notify.json

awslocal s3 cp data/judgment.docx s3://private-asset-bucket
