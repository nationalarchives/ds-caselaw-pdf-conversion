source .env

awslocal iam create-role \
  --role-name lambda-role \
  --assume-role-policy-document file://aws_examples/example_trust_policy.json

awslocal lambda create-function \
  --function-name pdf-lambda \
  --zip-file fileb://dist/lambda.zip \
  --handler ds-caselaw-pdf-conversion/lambda_function.handler \
  --runtime python3.9 \
  --environment "Variables={PUBLIC_ASSET_BUCKET=$PUBLIC_ASSET_BUCKET,AWS_SECRET_KEY=$AWS_SECRET_KEY,AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID,AWS_ENDPOINT_URL=$AWS_ENDPOINT_URL}" \
  --role arn:aws:iam::000000000000:role/lambda-role \

awslocal s3api create-bucket \
  --bucket public-asset-bucket
