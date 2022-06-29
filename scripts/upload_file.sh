source .env

for f in data/*.docx
do
 echo "Processing $f"
 awslocal s3 cp $f s3://private-asset-bucket
done
