source .env

awslocal iam create-role \
  --role-name lambda-role \
  --assume-role-policy-document file://aws_examples/example_trust_policy.json

awslocal lambda create-function \
  --function-name pdf-lambda \
  --zip-file fileb://dist/lambda.zip \
  --handler lambda_function.handler \
  --runtime python3.9 \
  --environment "Variables={PUBLIC_ASSET_BUCKET=$PUBLIC_ASSET_BUCKET,AWS_SECRET_KEY=$AWS_SECRET_KEY,AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID,AWS_ENDPOINT_URL=$AWS_ENDPOINT_URL}" \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --layers arn:aws:lambda:eu-west-2:764866452798:layer:libreoffice-gzip:1 \
  --memory-size 512 \
  --timeout 600

awslocal s3api create-bucket \
  --bucket public-asset-bucket

awslocal --endpoint-url=http://localhost:4566 \
s3api put-bucket-notification-configuration --bucket public-asset-bucket \
--notification-configuration file://aws_examples/s3/s3-notif-config.json
