import boto3
import json
from zipfile import ZipFile
from botocore.exceptions import ClientError

iam = boto3.resource('iam')
iam_client = boto3.client('iam')
client = boto3.client('lambda')

ACCOUNT_NUMBER = ""

LAMBDA_ROLE_NAME = "ecs_update_lambda"
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

LAMBDA_POLICY_NAME = "ecs_update_lambda"
LAMBDA_POLICY_DESCRIPTION = "This grants our lambdas the ability to start a new ECS task."
LAMBDA_POLICY_DOCUMENT = {
        "Version": "2012-10-17",
        'Statement': [
            {
                "Effect": "Allow",
                "Action": [
                    "ecs:RegisterTaskDefinition",
                    "ecs:UpdateService"
                ],
                "Resource": "*"
            },
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
                "Resource": "arn:aws:iam::" + ACCOUNT_NUMBER + ":role/*"
            },
            {
                "Action": [
                    "codepipeline:PutJobSuccessResult",
                    "codepipeline:PutJobFailureResult"
                ],
                "Effect": "Allow",
                "Resource": "*"
            }
        ]
    }

LAMBDA_POLICY_ARN = "arn:aws:iam::" + ACCOUNT_NUMBER + ":policy/" + LAMBDA_POLICY_NAME
LAMBDA_ROLE_ARN = "arn:aws:iam::" + ACCOUNT_NUMBER + ":role/" + LAMBDA_ROLE_NAME


def create_lambda_for_auto_deploy():

    # Create policy that lets Lambda update a task.
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

    # Create role for Lambda to assume.
    try:
        iam.create_role(RoleName=LAMBDA_ROLE_NAME,
                        AssumeRolePolicyDocument=json.dumps(LAMBDA_ROLE_POLICY_DOCUMENT))
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)

    iam_client.attach_role_policy(RoleName=LAMBDA_ROLE_NAME, PolicyArn=LAMBDA_POLICY_ARN)

    with ZipFile("lambda_code.zip", "w") as lambda_zip:
        lambda_zip.write("lambda_handler.py")
        lambda_zip.close()

    try:
        client.create_function(FunctionName="ecs_update",
                               Runtime="python3.6",
                               Code={"ZipFile": open("lambda_code.zip", "rb").read()},
                               Role=LAMBDA_ROLE_ARN,
                               Handler="lambda_handler.lambda_handler",
                               Publish=True
                               )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print("Object already exists")

            client.update_function_code(FunctionName="ecs_update",
                                        ZipFile=open("lambda_code.zip", "rb").read())

        else:
            print("Unexpected error: %s" % e)