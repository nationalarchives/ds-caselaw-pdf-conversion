source .env

awslocal s3 cp $1 s3://private-asset-bucket
