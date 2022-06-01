source .env

awslocal sqs create-queue --queue-name pdf-conversion-queue

awslocal s3api create-bucket \
  --bucket private-asset-bucket

awslocal s3 cp data/judgment.docx s3://private-asset-bucket
