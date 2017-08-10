import boto3
import json

iam = boto3.resource('iam')
iam_client = boto3.client('iam')


def create_role(role_name, trust_document):

    iam.create_role(RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_document))


def create_policy(policy_name, policy_document, policy_description):

    iam.create_policy(
        PolicyName=policy_name,
        PolicyDocument=json.dumps(policy_document),
        Description=policy_description
    )


def add_policy_to_role(role_name, policy_arn):
    iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn=policy_arn
        )
