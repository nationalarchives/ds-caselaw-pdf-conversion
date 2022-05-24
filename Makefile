build:
	@mkdir -p dist
	@STATIC_DEPS=true python3 -m pip install -t package -r requirements/base.txt
	@rm dist/lambda.zip & 2>&1
	@cd package && zip -r ../dist/lambda.zip * && cd ..
	@zip -g dist/lambda.zip ds-caselaw-pdf-conversion/lambda_function.py
	@echo 'Built dist/lambda.zip'

setup:
	make build
	sh scripts/setup-localstack.sh

update:
	make build
	@sh scripts/update-lambda.sh
