# http://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-access.html

import boto3
import json
from botocore.exceptions import ClientError
from iam import create_policy

key_client = boto3.client("kms")


def create_parameter_access_policy(stack_name, parameter_path, settings):
    parameter_policy_description = 'Give ECS access to parameters.'

    ecs_parameter_task_policy = {
        "Version": "2012-10-17",
        'Statement': [
            {
                "Sid": "keytask",
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameters"
                ],
                "Resource": "arn:aws:ssm:us-east-1:" + settings["ACCOUNT_NUMBER"] + ":parameter/" + parameter_path
            }
        ]
    }
    try:
        create_policy(stack_name + "-PARAMETER-ACCESS", ecs_parameter_task_policy, parameter_policy_description)
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)


def create_key_policy(policy_name):

    key_policy_description = 'Give ECS access to Keys for encrypting/decrypting.'

    ecs_key_task_policy_task = {
        "Version": "2012-10-17",
        'Statement': [
            {
                "Sid": "keytask",
                "Effect": "Allow",
                "Action": [
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:DescribeKey"
                ],
                "Resource": "*"
            }
        ]
    }

    create_policy(policy_name + "-KEY-USER", ecs_key_task_policy_task, key_policy_description)


def create_key(policy_name, settings):

    ecs_key_task_policy_admin = {
        "Version": "2012-10-17",
        'Statement': [
            {
                "Sid": "iam",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::" + settings["ACCOUNT_NUMBER"] + ":root"
                },
                "Action": "kms:*",
                "Resource": "*"
            },
            {
                "Sid": "keyadmin",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::" + settings["ACCOUNT_NUMBER"] + ":user/" + settings["KEY_ADMIN"]
                },
                "Action": [
                    "kms:Create*",
                    "kms:Describe*",
                    "kms:Enable*",
                    "kms:List*",
                    "kms:Put*",
                    "kms:Update*",
                    "kms:Revoke*",
                    "kms:Disable*",
                    "kms:Get*",
                    "kms:Delete*",
                    "kms:TagResource",
                    "kms:UntagResource",
                    "kms:ScheduleKeyDeletion",
                    "kms:CancelKeyDeletion"
                ],
                "Resource": "*"
            }
        ]
    }

    new_key = key_client.create_key(Policy=json.dumps(ecs_key_task_policy_admin))

    key_client.create_alias(
        AliasName="alias/" + policy_name + "-KEY",
        TargetKeyId=new_key["KeyMetadata"]["KeyId"]
    )


def get_keys_arn(key_name):

    alias_list = key_client.list_aliases()['Aliases']

    for alias in alias_list:
        if alias["AliasName"] == "alias/" + key_name:
            return alias["TargetKeyId"]


def secret_to_ps(ssm_client, secret_name, secret_value, key_name, dry_run):

    # Temporarily let's strip slashes out in favor of "."
    temp_secret_name = secret_name.replace("/", ".")

    if not dry_run:
        key_id = get_keys_arn(key_name)
        parameter_store_return = ssm_client.put_parameter(Name=temp_secret_name,
                                 Value=secret_value,
                                 Type="SecureString",
                                 KeyId=key_id,
                                 Overwrite=True)
        print(parameter_store_return)
        print(temp_secret_name)
        print("Written!")
    else:
        print(temp_secret_name)
        print(secret_value)