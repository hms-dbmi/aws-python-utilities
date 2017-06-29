from iam import create_role, add_policy_to_role
from botocore.exceptions import ClientError


def create_ecs_task_role(stack_name):
    ecs_trust_relationship = {
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    try:
        create_role(stack_name + "-TASK-ROLE", ecs_trust_relationship)
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)


def add_policy_to_ecs_task_role(stack_name, settings):
    decrypt_key_policy_arn = "arn:aws:iam::" + settings["ACCOUNT_NUMBER"] + ":policy/" + stack_name + "-KEY-USER"
    access_parameter_store_arn = "arn:aws:iam::" + settings["ACCOUNT_NUMBER"] + ":policy/" + stack_name + "-PARAMETER-ACCESS"

    add_policy_to_role(stack_name + "-TASK-ROLE", decrypt_key_policy_arn)
    add_policy_to_role(stack_name + "-TASK-ROLE", access_parameter_store_arn)


def create_ecs_cluster(ecs_client, cluster_name):
    print("Create ECS Cluster")
    ecs_client.create_cluster(clusterName=cluster_name)


def create_machine_tags(environment, stack_name, cluster_name, settings):

    return [{"Key": "owner", "Value": settings["MACHINE_OWNER"]},
                    {"Key": "environment", "Value": environment},
                    {"Key": "project", "Value": stack_name},
                    {"Key": "department", "Value": settings["GROUP_OWNER"]},
                    {"Key": "Name", "Value": cluster_name}]


def create_ecs_ec2(stack_name, cluster_name, vpc, ec2, userdata_string, settings, environment):

    print("Create EC2 for ECS")

    ec2_security_groups = list(vpc.security_groups.filter(Filters=[{'Name': 'tag:Name', 'Values': [stack_name + '_SG']}]))[0]

    subnet_id=""

    try:
        if settings["SUBNET_ID"]:
            subnet_id = settings["SUBNET_ID"]
    except KeyError:
        pass

    new_instance = create_ec2(ec2, settings, ec2_security_groups, userdata_string, subnet_id)
    machine_tags = create_machine_tags(environment, stack_name, cluster_name, settings)

    new_instance[0].create_tags(Tags=machine_tags)
    new_instance[0].wait_until_running()


def create_ec2(ec2, settings, ec2_security_groups, userdata_string, subnet_id):
    new_instance = ec2.create_instances(ImageId=settings['AMI_IMAGE_ID'],
                                        MinCount=1,
                                        MaxCount=1,
                                        InstanceType=settings['EC2_INSTANCE_TYPE'],
                                        SecurityGroupIds=[ec2_security_groups.id],
                                        KeyName=settings['EC2_KEY_NAME'],
                                        UserData=userdata_string,
                                        SubnetId=subnet_id,
                                        IamInstanceProfile={"Arn": settings['EC2_IAM_INSTANCE_PROFILE_ARN']},
                                        Placement={'AvailabilityZone': settings['AVAILABILITY_ZONE'],
                                                   'Tenancy': settings['TENANCY']})
    return new_instance


def create_ecs_task(ecs_client, task_family, cluster_name, settings, environment, taskname, taskrole=None):

    print("Create ECS Task " + environment + " " + taskname)

    vault_path = settings["VAULT_PROJECT_NAME"] + '/' + taskname.lower() + "/" + environment
    db_vault_path = ""

    try:
        if settings["DB_VAULT_PROJECT_NAME"]:
            db_vault_path = settings["DB_VAULT_PROJECT_NAME"] + "/" + environment + "/"
    except KeyError:
        pass

    app_image_enviro_repo = settings["APP_IMAGE_REPO_" + taskname + "_" + environment.upper()]

    container_port_mappings = []

    for port_mapping in settings[taskname + "_PORT"].split(","):
        container_port_mappings.append({'hostPort': int(port_mapping), 'containerPort': int(port_mapping)})

    container_definition = [{
        'name': cluster_name + "_" + taskname,
        'image': app_image_enviro_repo,
        'memoryReservation': int(settings["CONTAINER_MEMORY_RESERVATION"]),
        'memory': int(settings["CONTAINER_MEMORY"]),
        'portMappings': container_port_mappings,
        'environment': [{'name': 'VAULT_ADDR', 'value': settings["VAULT_URL"]},
                        {'name': 'VAULT_PATH', 'value': vault_path},
                        {'name': 'PS_PATH', 'value': vault_path.replace("/", ".")},
                        {'name': 'DB_VAULT_PATH', 'value': db_vault_path},
                        {'name': 'VAULT_SKIP_VERIFY', 'value': '1'}]
    }]

    try:
        if settings["INCLUDE_ECS_CLOUDWATCH"] == "True":
            container_definition[0]["logConfiguration"] = {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": settings["CLOUDWATCH_GROUP"] + environment,
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": settings["CLOUDWATCH_PREFIX"]
                }
            }
    except KeyError:
        pass

    ecs_client.register_task_definition(family=task_family + "-" + taskname,
                                        taskRoleArn=taskrole,
                                        containerDefinitions=container_definition)


def create_ecs_service(ecs_client, cluster_name, task_definition):

    ecs_client.create_service(cluster=cluster_name,
                              serviceName=task_definition,
                              taskDefinition=task_definition,
                              desiredCount=1,
                              deploymentConfiguration={
                                  'maximumPercent': 100,
                                  'minimumHealthyPercent': 0
                              }
                              )
