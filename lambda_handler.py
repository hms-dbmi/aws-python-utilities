import boto3
import json
ecs_client = boto3.client('ecs')
codepipeline_client = boto3.client('codepipeline')


def lambda_handler(event, context):

    event_from_pipeline = event["CodePipeline.job"]["data"]["actionConfiguration"]["configuration"]["UserParameters"]

    decoded_params = json.loads(event_from_pipeline)

    try:

        environment = decoded_params["ENVIRONMENT"]
        taskname = decoded_params["TASKNAME"]
        task_family = decoded_params["TASK_FAMILY"]
        task_role = decoded_params["TASK_ROLE"]
        cluster_name = decoded_params["CLUSTER_NAME"]
        ps_path = decoded_params["PS_PATH"]
        db_secret_path = decoded_params["DB_SECRET_PATH"]
        include_cloudwatch = decoded_params["INCLUDE_CLOUDWATCH"]
        container_memory = decoded_params["CONTAINER_MEMORY"]
        container_memory_reservation = decoded_params["CONTAINER_MEMORY_RESERVATION"]
        cloudwatch_group = decoded_params["CLOUDWATCH_GROUP"]
        cloudwatch_prefix = decoded_params["CLOUDWATCH_PREFIX"]
        app_image_repo = decoded_params["APP_IMAGE_REPO"]
        ports = decoded_params["PORTS"]

    except KeyError:
        codepipeline_client.put_job_failure_result(
            jobId=event["CodePipeline.job"]["id"],
            failureDetails={"type": "ConfigurationError", "message": "Missing Parameters!"}
        )

    secret_path = ps_path + "/" + environment

    container_port_mappings = []

    for port_mapping in ports.split(","):
        container_port_mappings.append({'hostPort': int(port_mapping), 'containerPort': int(port_mapping)})

    container_definition = [{
        'name': cluster_name + "_" + taskname,
        'image': app_image_repo,
        'memoryReservation': int(container_memory_reservation),
        'memory': int(container_memory),
        'portMappings': container_port_mappings,
        'environment': [
                        {'name': 'PS_PATH', 'value': secret_path.replace("/", ".")},
                        {'name': 'DB_VAULT_PATH', 'value': db_secret_path},
                        {'name': 'VAULT_SKIP_VERIFY', 'value': '1'}]
    }]

    try:
        if include_cloudwatch == "True":
            container_definition[0]["logConfiguration"] = {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": cloudwatch_group + environment.lower(),
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": cloudwatch_prefix
                }
            }
    except KeyError:
        pass

    print("Register task definition.")
    ecs_client.register_task_definition(family=task_family + "-" + taskname,
                                        taskRoleArn=task_role,
                                        containerDefinitions=container_definition)

    print("Update Service.")
    ecs_client.update_service(cluster=cluster_name,
                              service=cluster_name,
                              taskDefinition=cluster_name + "-" + taskname)

    codepipeline_client.put_job_success_result(
        jobId=event["CodePipeline.job"]["id"]
    )

    return {
        'message': "Success! Task Updated (" + cluster_name + "-" + taskname + ") in service " + cluster_name + "."
    }
