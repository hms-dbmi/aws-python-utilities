import boto3

from iam import create_policy, create_role, add_policy_to_role
from botocore.exceptions import ClientError

codebuild_client = boto3.client('codebuild')

codebuild_trust_relationship = {
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "codebuild.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}


def create_role_and_policy_for_codebuild(project_name, settings):

    codebuild_service_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:logs:us-east-1:685606823951:log-group:/aws/codebuild/" + project_name,
                    "arn:aws:logs:us-east-1:685606823951:log-group:/aws/codebuild/" + project_name + ":*"
                ],
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ]
            },
            {
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:s3:::codepipeline-us-east-1-*"
                ],
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:GetObjectVersion"
                ]
            },
            {
                "Action": [
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:CompleteLayerUpload",
                    "ecr:GetAuthorizationToken",
                    "ecr:InitiateLayerUpload",
                    "ecr:PutImage",
                    "ecr:UploadLayerPart"
                ],
                "Resource": "*",
                "Effect": "Allow"
            }
        ]
    }

    try:
        create_policy("CODEBUILD-" + project_name + "-SERVICE-POLICY", codebuild_service_role_policy,"CODEBUILD-" + project_name + "-SERVICE-ROLE")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)

    try:
        create_role("CODEBUILD-" + project_name + "-SERVICE-ROLE", codebuild_trust_relationship)
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)

    add_policy_to_role("CODEBUILD-" + project_name + "-SERVICE-ROLE", "arn:aws:iam::" + settings["ACCOUNT_NUMBER"] + ":policy/CODEBUILD-" + project_name + "-SERVICE-POLICY")


def create_codebuild(project_name, task_name, image_tag, settings):
    create_role_and_policy_for_codebuild(project_name, settings)

    try:
        codebuild_client.create_project(name=project_name,
                                        source={"type": "CODEPIPELINE"},
                                        artifacts={"type": "CODEPIPELINE"},
                                        environment={"type": "LINUX_CONTAINER",
                                                     "image": "aws/codebuild/docker:1.12.1",
                                                     "computeType": "BUILD_GENERAL1_MEDIUM",
                                                     "environmentVariables": [
                                                         {"name": "AWS_DEFAULT_REGION", "value": "us-east-1"},
                                                         {"name": "AWS_ACCOUNT_ID",
                                                          "value": settings["ACCOUNT_NUMBER"]},
                                                         {"name": "IMAGE_REPO_NAME", "value": task_name},
                                                         {"name": "IMAGE_TAG", "value": image_tag}]},
                                        serviceRole="CODEBUILD-" + project_name + "-SERVICE-ROLE")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            print("Error: %s" % e)
        else:
            print("Error: %s" % e)



