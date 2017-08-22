import boto3
import json
from zipfile import ZipFile
from botocore.exceptions import ClientError

iam = boto3.resource('iam')
iam_client = boto3.client('iam')
client = boto3.client('lambda')


def deploy_lambda(account_number, lambda_prefix, lambda_description, lambda_code_location):

    LAMBDA_ROLE_NAME = lambda_prefix + "_lambda_role_name"
    LAMBDA_ROLE_POLICY_DOCUMENT = {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

    LAMBDA_POLICY_NAME = lambda_prefix + "_lambda_policy_name"
    LAMBDA_POLICY_DESCRIPTION = lambda_description
    LAMBDA_POLICY_DOCUMENT = {
            "Version": "2012-10-17",
            'Statement': [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": [
                        "arn:aws:logs:*:*:*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:PassRole"
                    ],
                    "Resource": "arn:aws:iam::" + account_number + ":role/*"
                }
            ]
        }

    LAMBDA_POLICY_ARN = "arn:aws:iam::" + account_number + ":policy/" + LAMBDA_POLICY_NAME
    LAMBDA_ROLE_ARN = "arn:aws:iam::" + account_number + ":role/" + LAMBDA_ROLE_NAME

    print("Creating policy.")

    try:
        iam.create_policy(
            PolicyName=LAMBDA_POLICY_NAME,
            PolicyDocument=json.dumps(LAMBDA_POLICY_DOCUMENT),
            Description=LAMBDA_POLICY_DESCRIPTION
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)

    print("Creating role.")

    try:
        iam.create_role(RoleName=LAMBDA_ROLE_NAME,
                        AssumeRolePolicyDocument=json.dumps(LAMBDA_ROLE_POLICY_DOCUMENT))
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)

    print("Attaching role.")

    try:
        iam_client.attach_role_policy(RoleName=LAMBDA_ROLE_NAME, PolicyArn=LAMBDA_POLICY_ARN)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ClientError':
            print("Object already attached")
        else:
            print("Unexpected error: %s" % e)

    print("Zipping lambda code.")

    with ZipFile("lambda_code.zip", "w") as lambda_zip:
        lambda_zip.write(lambda_code_location, "lambda_handler.py")
        lambda_zip.close()

    print("Creating lambda function.")

    try:
        return client.create_function(FunctionName=lambda_prefix,
                               Runtime="python3.6",
                               Code={"ZipFile": open("lambda_code.zip", "rb").read()},
                               Role=LAMBDA_ROLE_ARN,
                               Handler="lambda_handler.lambda_handler",
                               Publish=True
                               )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print("Object already exists")

            return client.update_function_code(FunctionName=lambda_prefix,
                                        ZipFile=open("lambda_code.zip", "rb").read())

        else:
            print("Unexpected error: %s" % e)
