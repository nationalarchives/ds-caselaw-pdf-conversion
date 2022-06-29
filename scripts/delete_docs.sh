source .env

awslocal s3 rm s3://private-asset-bucket/judgment.docx
awslocal s3 rm s3://private-asset-bucket/judgment.pdf
