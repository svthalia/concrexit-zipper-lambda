from urllib.parse import urlparse
import zipfile
import tempfile
import shutil
import json
import os
import requests
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    # DSN will be read from environment.
    integrations=[
        AwsLambdaIntegration(timeout_warning=True),
    ],
    traces_sample_rate=1.0,
    profiles_sample_rate=0.1,
)


def handler(event, context):
    """Lambda function that will extract face encodings from a photo."""
    if not (
        isinstance(event.get("api_url"), str)
        and isinstance(event.get("upload_url", str))
        and isinstance(event.get("token"), str)
        and isinstance(event.get("sources"), list)
    ):
        raise ValueError("Bad event data.")

    upload_url = event["upload_url"]
    token = event["token"]
    sources = event["sources"]

    for source in sources:
        if not (isinstance(source, str)):
            raise ValueError("Bad event data.")
    temp_dir = tempfile.mkdtemp(prefix=token)

    try:
        downloadFiles(sources, temp_dir)
        # Create a zip file of the downloaded images (without the directory structure)
        zip_filename = f'/tmp/{token}.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), file)

        # We have retrieved the full zip file of the images, now we upload to the signed URL? The code was found https://beabetterdev.com/2021/09/30/aws-s3-presigned-url-upload-tutorial-in-python/ as I have no experience with presigned URLs or S3 
        files = {'file': open(zip_filename, 'rb')}
        res = requests.post(upload_url, files=files)
        res.raise_for_status()

        # Return a successful response
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Images zipped and uploaded"})
        }
    except Exception as e:
        # Catch any other unexpected errors
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
    finally:
        # Clean up temporary directory after processing
        shutil.rmtree(temp_dir)

def downloadFiles(sources, temp_dir):
    # Download images to temporary directory
    for source in sources:
        response = requests.get(source, timeout=15)
        response.raise_for_status()

        # Get filename from the URL
        parsed_url = urlparse(source)
        file_name = os.path.basename(parsed_url.path)

        # Save image file to temp directory
        with open(os.path.join(temp_dir, file_name), 'wb') as f:
            f.write(response.content)