# ds-caselaw-pdf-conversion

This is the repository for the lambda function used to convert `docx` judgments into `pdf`

## Development

We're using [localstack](https://github.com/localstack/localstack), along with the awslocal-cli to enable local development of the lambda function.

### Requirements

An installation of `make` is required to use the bundled Makefile for local development. Most operating systems come with this preinstalled, including Ubuntu Linux and MacOS. On Windows, Make can be installed via the Chocolatey package manager, or using the Windows Subsystem for Linux (WSL).

You will also need both `awscli` and `awslocal-cli` installed. `awslocal-cli` is a `Localstack`-specific wrapper around `awscli`.

Install both from the requirements file using:

```bash
python3 -m pip install -r requirements/local.txt
```

### Setup Localstack

First, copy `.env.example` to `.env` and fill in the missing variables. If you are using Localstack via Docker, leave `MARKLOGIC_HOST` as `host.docker.internal`.

Then, start Localstack using:

```bash
docker-compose up -d
```

This will start Localstack in detached mode; logs are accessible via Docker Desktop.

Once the docker container is running, use the following make command to build a distribution of the lambda function, and setup the localstack AWS services

```bash
make setup
```

This will create a folder, `dist`, on your local machine that contains a zip file called `lambda.zip` - this is our compiled lambda. You can also upload this directly to the AWS console.
