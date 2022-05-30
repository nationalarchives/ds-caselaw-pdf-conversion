build:
	@mkdir -p dist
	@STATIC_DEPS=true python3 -m pip install -t package -r requirements/base.txt
	@rm dist/lambda.zip & 2>&1
	@cd package && zip -r ../dist/lambda.zip * && cd ..
	@cd ds-caselaw-pdf-conversion && zip -g ../dist/lambda.zip lambda_function.py && cd ..
	@zip -g dist/lambda.zip fonts
	@echo 'Built dist/lambda.zip'

setup:
	make build
	sh scripts/setup-localstack.sh

update:
	make build
	@sh scripts/update-lambda.sh

lambda:
	@cd ds-caselaw-pdf-conversion && zip -g ../dist/lambda.zip lambda_function.py && cd ..
	@zip -g dist/lambda.zip fonts
	@echo 'Built dist/lambda.zip'
	@sh scripts/update-lambda.sh

onlylambda:
	@cd ds-caselaw-pdf-conversion && zip -g ../dist/lambda.zip lambda_function.py && cd ..
	@zip -g dist/lambda.zip fonts
	@echo 'Built dist/lambda.zip'

upload:
	awslocal s3 cp aws_examples/s3/public-asset-bucket/judgment.docx s3://public-asset-bucket
