import boto3

from lambda_deploy import deploy_lambda
from cloudwatch import create_healthcheck_alarm

# Create a lambda (and associated permissions), add an event to trigger it every minute, add an alarm when it fails.
def create_health_check_lambda(account_number, naming_prefix, lambda_code_location, lambda_input, alert_action_arn):

    new_lambda = deploy_lambda(account_number, naming_prefix, "Lambda to test sites to see if they are up.", lambda_code_location)

    event_client = boto3.client('events')
    event_client.put_rule(Name=naming_prefix + "-hc", ScheduleExpression='rate(1 minute)', EventPattern="")

    event_client.put_targets(
        Rule=naming_prefix + '-hc',
        Targets=[
            {
                'Arn': new_lambda['FunctionArn'],
                'Id': naming_prefix + "-hc",
                'Input': lambda_input
            }
        ]
    )

    create_healthcheck_alarm(naming_prefix, naming_prefix, alert_action_arn)


# Route53 Healthcheck, we don't use this right now because it's too frequent in its pings.
def create_health_check(health_check_name, domain, port, path, interval):
    
    health_check_config = {'Port': port,
                           'Type': "HTTPS",
                           'ResourcePath': path,
                           'FullyQualifiedDomainName': domain,
                           'RequestInterval': interval}

    route53_client.create_health_check(CallerReference=health_check_name, HealthCheckConfig=health_check_config)