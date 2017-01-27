import time

def create_security_groups(stack_name, vpc, settings):

    protected_cidr = settings["PROTECTED_CIDR"]

    print("Creating Security Groups")
    security_group_name = stack_name + '_SG'
    security_group_description = stack_name + ' HTTP/HTTPS/SSH SG'

    new_security_group = vpc.create_security_group(GroupName=security_group_name,
                                                   Description=security_group_description)

    time.sleep(5)

    new_security_group.create_tags(Tags=[{'Key': 'Name', 'Value': security_group_name}])

    new_security_group.authorize_ingress(CidrIp=protected_cidr, FromPort=443, ToPort=443, IpProtocol="tcp")


def create_db_security_groups(stack_name, vpc):

    print("Database Security Group")
    db_security_group_name = stack_name + '_DB_SG'
    db_security_group_description = stack_name + ' APP to DB SG'

    # Grab the Web App security group.
    new_security_group = list(vpc.security_groups.filter(Filters=[{'Name': 'tag:Name', 'Values': [stack_name + '_SG']}]))[0]

    new_db_security_group = vpc.create_security_group(GroupName=db_security_group_name, Description=db_security_group_description)

    new_db_security_group.create_tags(Tags=[{'Key': 'Name', 'Value': db_security_group_name}])

    # Allow 1521 access from WebApp Security Group.
    new_db_security_group_ip_perm = [{"IpProtocol": 'tcp', "UserIdGroupPairs": [{"GroupId": new_security_group.id}], "FromPort": 3306, "ToPort": 3306}]
    new_db_security_group.authorize_ingress(IpPermissions=new_db_security_group_ip_perm)