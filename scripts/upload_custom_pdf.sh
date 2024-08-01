source .env

awslocal s3 cp data/judgment.pdf s3://private-asset-bucket --metadata '{"pdfsource": "custom-pdfs"}'
