# ds-caselaw-pdf-conversion

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
