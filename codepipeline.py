from botocore.exceptions import ClientError
from iam import create_policy, create_role
import json
import boto3

codepipeline_client = boto3.client('codepipeline')

CODE_PIPELINE_TRUST_RELATIONSHIP = {
    "Version": "2012-10-17",
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


def create_pipeline(stack_name, environment, task_name, settings, paramter_store_path):

    policy_name = stack_name + "-CODE-PIPELINE-POLICY"
    role_name = stack_name + "-CODE-PIPELINE-ROLE"
    ecs_task_role = "arn:aws:iam::" + settings["ACCOUNT_NUMBER"] + ":role/" + stack_name + "-" + task_name + "-TASK-ROLE"

    artifact_name_to_pass = task_name.lower() + "-app"

    update_ecs_lambda_parameters = {"ENVIRONMENT": environment,
                                    "TASKNAME": task_name,
                                    "TASK_FAMILY": stack_name,
                                    "TASK_ROLE": ecs_task_role,
                                    "CLUSTER_NAME": stack_name,
                                    "PS_PATH": paramter_store_path,
                                    "DB_SECRET_PATH": "",
                                    "INCLUDE_CLOUDWATCH": "True",
                                    "CONTAINER_MEMORY": settings["CONTAINER_MEMORY"],
                                    "CONTAINER_MEMORY_RESERVATION": settings["CONTAINER_MEMORY_RESERVATION"],
                                    "CLOUDWATCH_GROUP": settings["CLOUDWATCH_GROUP"],
                                    "CLOUDWATCH_PREFIX": settings["CLOUDWATCH_PREFIX"] + "-",
                                    "APP_IMAGE_REPO": settings["APP_IMAGE_REPO_" + task_name + "_" + environment],
                                    "PORTS": settings[task_name + "_PORT"]
                                    }

    code_pipe_line_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:logs:us-east-1:" + settings["ACCOUNT_NUMBER"] + ":log-group:/aws/codebuild/" + stack_name.lower() + ":*"
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
            }
        ]
    }

    code_pipeline_configuration = {
        "stages": [
            {
                "actions": [
                    {
                        "runOrder": 1,
                        "actionTypeId": {
                            "category": "Source",
                            "provider": "GitHub",
                            "version": "1",
                            "owner": "ThirdParty"
                        },
                        "name": "Source",
                        "outputArtifacts": [
                            {
                                "name": artifact_name_to_pass
                            }
                        ],
                        "configuration": {
                            "Branch": "development",
                            "OAuthToken": settings["GITHUB_OAUTH_TOKEN"],
                            "Owner": "hms-dbmi",
                            "Repo": settings["REPO_NAME_" + task_name]
                        },
                        "inputArtifacts": []
                    }
                ],
                "name": "Source"
            },
            {
                "actions": [
                    {
                        "runOrder": 1,
                        "actionTypeId": {
                            "category": "Build",
                            "provider": "CodeBuild",
                            "version": "1",
                            "owner": "AWS"
                        },
                        "name": "CodeBuild",
                        "outputArtifacts": [
                            {
                                "name": "MyAppBuild"
                            }
                        ],
                        "configuration": {
                            "ProjectName": stack_name + "-" + task_name
                        },
                        "inputArtifacts": [
                            {
                                "name": artifact_name_to_pass
                            }
                        ]
                    }
                ],
                "name": "Build"
            },
            {
                "name": "Deploy",
                "actions": [
                    {
                        "outputArtifacts": [],
                        "inputArtifacts": [],
                        "runOrder": 1,
                        "actionTypeId": {
                            "version": "1",
                            "category": "Invoke",
                            "provider": "Lambda",
                            "owner": "AWS"
                        },
                        "name": "Deploy_Lambda",
                        "configuration": {
                            "FunctionName": "ecs_update",
                            "UserParameters": json.dumps(update_ecs_lambda_parameters)
                        }
                    }
                ]
            }
        ],
        "artifactStore": {
            "type": "S3",
            "location": "codepipeline-us-east-1-24805390581"
        },
        "name": task_name.lower() + "-" + environment.lower(),
        "roleArn": "arn:aws:iam::" + settings["ACCOUNT_NUMBER"] + ":role/AWS-CodePipeline-Service"
    }

    try:
        create_policy(policy_name, code_pipe_line_policy, "Allow code pipeline access to S3/logs.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)

    try:
        create_role(role_name, CODE_PIPELINE_TRUST_RELATIONSHIP)
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)

    try:
        codepipeline_client.create_pipeline(pipeline=code_pipeline_configuration)
    except ClientError as e:
        if e.response['Error']['Code'] == 'PipelineNameInUseException':
            print("Object already exists")
            codepipeline_client.update_pipeline(pipeline=code_pipeline_configuration)
        else:
            print("Unexpected error: %s" % e)
