import time
from botocore.exceptions import ClientError

def create_security_groups(stack_name, vpc, settings):

    print("Creating Security Groups")
    security_group_name = stack_name + '_SG'
    security_group_description = stack_name + ' HTTP/HTTPS/SSH SG'

    new_security_group = vpc.create_security_group(GroupName=security_group_name, Description=security_group_description)

    time.sleep(5)

    new_security_group.create_tags(Tags=[{'Key': 'Name', 'Value': security_group_name}])

    return new_security_group


def create_db_security_groups(stack_name, vpc):

    print("Database Security Group")
    db_security_group_name = stack_name + '_DB_SG'
    db_security_group_description = stack_name + ' APP to DB SG'

    # Grab the Web App security group.
    new_security_group = list(vpc.security_groups.filter(Filters=[{'Name': 'tag:Name', 'Values': [stack_name + '_SG']}]))[0]

    new_db_security_group = vpc.create_security_group(GroupName=db_security_group_name, Description=db_security_group_description)

    new_db_security_group.create_tags(Tags=[{'Key': 'Name', 'Value': db_security_group_name}])

    # Allow 3306 access from WebApp Security Group.
    new_db_security_group_ip_perm = [{"IpProtocol": 'tcp', "UserIdGroupPairs": [{"GroupId": new_security_group.id}], "FromPort": 3306, "ToPort": 3306}]
    new_db_security_group.authorize_ingress(IpPermissions=new_db_security_group_ip_perm)


def add_ingress_to_sg(stack_name, vpc, cidr_ip, from_port, to_port):

    security_group = list(vpc.security_groups.filter(Filters=[{'Name': 'tag:Name', 'Values': [stack_name + '_SG']}]))[0]

    try:
        security_group.authorize_ingress(CidrIp=cidr_ip, FromPort=from_port, ToPort=to_port, IpProtocol="tcp")
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)


def add_sg_ingress_to_sg(sg_name, vpc, source_security_group_name, from_port, to_port):

    origin_sg = list(vpc.security_groups.filter(Filters=[{'Name': 'tag:Name', 'Values': [source_security_group_name]}]))[0]
    destination_sg = list(vpc.security_groups.filter(Filters=[{'Name': 'tag:Name', 'Values': [sg_name]}]))[0]

    security_group_ip_perm = [{"IpProtocol": 'tcp', "UserIdGroupPairs": [{"GroupId": origin_sg.id}], "FromPort": from_port, "ToPort": to_port}]

    print(security_group_ip_perm)

    try:
        destination_sg.authorize_ingress(IpPermissions=security_group_ip_perm)
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print("Object already exists")
        else:
            print("Unexpected error: %s" % e)
