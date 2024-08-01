# The National Archives: Find Case Law

This repository is part of the [Find Case Law](https://caselaw.nationalarchives.gov.uk/) project at [The National Archives](https://www.nationalarchives.gov.uk/). For more information on the project, check [the documentation](https://github.com/nationalarchives/ds-find-caselaw-docs).

# PDF Conversion Service

When a file is uploaded to the S3 bucket and ends in .docx, create a PDF file at the same key (but ending .pdf instead).
Uses LibreOffice to perform the conversion.

## Deployment

### Staging

The `main` branch is automatically deployed to staging with each commit.

### Production

To deploy to production:

1. Create a [new release](https://github.com/nationalarchives/ds-caselaw-pdf-conversion/releases).
2. Set the tag and release name to `vX.Y.Z`, following semantic versioning.
3. Publish the release.
4. Automated workflow will then force-push that release to the `production` branch, which will then be deployed to
   the production environment.

## Republishing PDFs

You can republish a PDF by uploading the PDF again, or by sending JSON of the form:

```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "tna-caselaw-assets"
        },
        "object": {
          "key": "eat/2022/1/eat_2022_1.docx",
          "eTag": "fa2ef6e8abadbd5cc5cedf3f32834f1f"
        }
      }
    }
  ]
}
```

to the Send and Receive Messages page of the Simple Queuing System on AWS.

The script scripts/create_json_for_bulk_pdf_regeneration will make that JSON
file for you, if you want to remake every PDF that's backed by a docx file.

(The eTag is arbitrary but should be a sensible filename fragment, no / )

## Local setup

1. Copy `.env.example` to `.env`
2. From ds-caselaw-ingester, run `docker compose up` to launch the Localstack container
3. From ds-caselaw-pdfconversion, run `scripts/setup-localstack.sh` to set up the queues etc.
4. From ds-caselaw-pdfconversion, run `docker compose up --build` to launch the LibreOffice container
   (`--build` will ensure the converter script is in the docker container)

You might want to look at the [localstack S3 bucket](http://localhost:4566/private-asset-bucket)

### Local testing

`pytest queue_listener/tests.py` will run unit tests.

Manual integration tests, having run Local Start up tasks above:

You should see output like:

```
Downloading judgment.docx
...
Uploaded judgment.pdf
```

on startup.

#### Scripts

`upload_file` will upload a docx, which should generate a PDF

`upload_custom_pdf` will upload a tagged PDF, which should cause `upload_file` to fail with `judgment.pdf is from custom-pdfs, not replacing`

`upload_named_pdf` will upload a docx of your choosing
