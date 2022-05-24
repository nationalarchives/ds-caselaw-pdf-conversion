source .env

awslocal lambda update-function-code --function-name pdf-lambda --zip-file fileb://dist/lambda.zip

awslocal lambda update-function-configuration --function-name pdf-lambda \
    --environment "Variables={PUBLIC_ASSET_BUCKET=$PUBLIC_ASSET_BUCKET,AWS_SECRET_KEY=$AWS_SECRET_KEY,AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID,AWS_ENDPOINT_URL=$AWS_ENDPOINT_URL}"
