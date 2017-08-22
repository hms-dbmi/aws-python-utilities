import boto3

cloudwatch = boto3.client('cloudwatch')


def create_healthcheck_alarm(alarm_name, lambda_name, alarm_action):

    print("Create Alarm.")

    cloudwatch.put_metric_alarm(
        AlarmName=alarm_name,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        EvaluationPeriods=1,
        MetricName='Errors',
        Namespace='AWS/Lambda',
        Period=60,
        Statistic='Average',
        Threshold=0.0,
        ActionsEnabled=True,
        AlarmDescription='Alarm when healthcheck Lambda is throwing errors.',
        Dimensions=[
            {
                'Name': 'FunctionName',
                'Value': lambda_name
            },
        ],
        Unit='Seconds',
        TreatMissingData="missing",
        AlarmActions=[alarm_action]
    )
