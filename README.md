# concrexit-zipper

An AWS Lambda function that creates a zip of pictures for photo albums [svthalia/concrexit](https://github.com/svthalia/concrexit).

## Usage

This function is meant to be invoked with an [AWS API call](https://docs.aws.amazon.com/lambda/latest/dg/API_Invoke.html).

From python, this can be done with [`boto3`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/invoke.html), given the `InvokeFunction` permission:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "<lambda-arn>"
    }
  ]
}
```

The function expects a payload as follows (at least one source):

```json
{
    "api_url": "https://thalia.nu",
    "upload_url": "the signed url to upload the zip file",
    "token": "base64 token for authentication",
    "sources": [
        "any amount of urls to download photo file from",
        ...
    ]
}
```

If everything goes right, the function will POST a zip file to the `upload_url` sent to the lambda. The function returns a response with statuscode 200 containing:
    
```json
{
    "message": "Images zipped and uploaded"
}
```

## Deployment

Deploying this function takes a few steps:

1. First, there needs to be an AWS Elastic Container Registry (ECR) repository to store the Docker image in. 
  We assume that this is created manually and has the name `concrexit/facedetection-lambda`. See https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-console.html. 
2. Then, whenever changes are made, the Docker image needs to be built and pushed to the ECR repository. Right now, the images are pushed with the `latest` tag. See https://docs.aws.amazon.com/lambda/latest/dg/images-create.html#images-create-from-base. There is a GitHub workflow that does this automatically on push to `main`. At some point, we could change this to push to e.g. `production` and `staging` tags separately.
3. Finally, the Lambda function needs to be created (or updated). This is done using Terraform. See below.
  
To use Terraform, you need to have the AWS CLI installed (https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli), and have AWS IAM user credentials configured, with a `~/.aws/credentials` file that looks like this:

```
[thalia]
aws_access_key_id=***
aws_secret_access_key=*****
```

Then, assuming the ECR repository exists, and the Docker image has been pushed, you can run `terraform init` and `terraform apply` to create or update the Lambda functions (in one of the two stages). Terraform will look up the exact image that has the latest tag right now, and use that.

Terraform will output the ARN of the function. The idea is that concrexit staging should be using the staging function, and concrexit production should be using the production function. 

These ARNs need to be passed as settings and to Terraform in `[svthalia/concrexit](https://github.com/svthalia/concrexit) to give the servers permission to invoke the functions, and to tell concrexit which function to use. The ARN does not change when the function is updated, so this only needs to be done once.

Then, you can invoke the function with curl:
```sh
curl -XPOST "http://localhost:8000/" -d '{
    "api_url": "https://thalia.nu",
    "upload_url": "https://thalia.nu/files/aaaaa.zip",
    "token": "123abc",
    "sources": [
        "any amount of urls to download photo file from",
        ...
    ]
}
```