import hvac
import random
import string
import MySQLdb

def retrieve_subnet_ids_by_name(name_list, vpc):

    idlist = []

    subnet_list = vpc.subnets.filter(Filters=[{'Name': 'tag:Name', 'Values': name_list}])

    for single_subnet in subnet_list:
        idlist.append(single_subnet.id)

    return idlist


def create_db_subnet(stack_name, rds_client, vpc):
    db_subnet_group_name = stack_name.lower()

    db_subnet_ids = retrieve_subnet_ids_by_name([stack_name + "_DB_1", stack_name + "_DB_2"], vpc)

    rds_client.create_db_subnet_group(DBSubnetGroupName=db_subnet_group_name,
                                      DBSubnetGroupDescription=db_subnet_group_name,
                                      SubnetIds=db_subnet_ids)


def create_db(stack_name, vpc, rds_client, settings, environment, task_name):
    db_subnet_group_name = stack_name.lower()

    print("Create RDS Instance")

    # Grab the DB Security Group.
    db_security_groups = [list(vpc.security_groups.filter(Filters=[{'Name': 'tag:Name', 'Values': [stack_name + '_DB_SG']}]))[0].id]

    db_tags = [{"Key": "owner", "Value": settings["MACHINE_OWNER"]},
               {"Key": "environment", "Value": environment},
               {"Key": "project", "Value": stack_name},
               {"Key": "department", "Value": settings["GROUP_OWNER"]}]

    db_instance_identifier = stack_name + "-db"

    db_master_user_password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))

    rds_client.create_db_instance(DBName=settings['DB_NAME'],
                                  DBInstanceIdentifier=db_instance_identifier,
                                  DBInstanceClass=settings['DB_INSTANCE_CLASS'],
                                  AllocatedStorage=int(settings['DB_ALLOCATED_STORAGE']),
                                  Engine=settings['DB_ENGINE'],
                                  MasterUsername=settings['DB_MASTER_USERNAME'],
                                  MasterUserPassword=db_master_user_password,
                                  AvailabilityZone=settings['DB_AVAILABILITY_ZONE'],
                                  DBSubnetGroupName=db_subnet_group_name,
                                  EngineVersion=settings['DB_ENGINE_VERSION'],
                                  LicenseModel=settings['DB_LICENSE_MODEL'],
                                  PubliclyAccessible=(settings['DB_PUBLICY_ACCESSIBLE'] == 'True'),
                                  Tags=db_tags,
                                  StorageType=settings['DB_STORAGE_TYPE'],
                                  StorageEncrypted=(settings['DB_STORAGE_ENCRYPTED'] == 'True'),
                                  CopyTagsToSnapshot=(settings['DB_COPY_TAGS'] == 'True'),
                                  VpcSecurityGroupIds=db_security_groups)

    # Wait for the database to become ready.
    waiter = rds_client.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier=db_instance_identifier)

    new_db_info = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)

    # Add Database Info to Vault
    vault_path = settings["VAULT_PROJECT_NAME"] + "/" + task_name.lower() + "/" + environment.lower() + "/"

    vault_client = hvac.Client(url=settings["VAULT_URL"], token=settings["VAULT_TOKEN"], verify=False)

    print("[DEBUG] Writing Secret " + vault_path + "mysql_host")
    print("[DEBUG] Writing Secret " + vault_path + "mysql_pw")

    vault_client.write(vault_path + "mysql_host", value=new_db_info['DBInstances'][0]['Endpoint']['Address'])
    vault_client.write(vault_path + "mysql_pw", value=db_master_user_password)


def create_database_for_task(settings, root_task_name, task_name, environment):

    vault_path = settings["VAULT_PROJECT_NAME"] + "/" + root_task_name.lower() + "/" + environment.lower() + "/"

    vault_client = hvac.Client(url=settings["VAULT_URL"], token=settings["VAULT_TOKEN"], verify=False)

    mysql_username = "root"
    mysql_host = vault_client.read(vault_path + "mysql_host")["data"]["value"]
    mysql_pw = vault_client.read(vault_path + "mysql_pw")["data"]["value"]

    db1 = MySQLdb.connect(host=mysql_host, user=mysql_username, passwd=mysql_pw)

    db_user_password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))

    sql_db = 'CREATE DATABASE ' + task_name.lower()
    sql_user = "CREATE USER '" + task_name.lower() + "' IDENTIFIED BY '" + db_user_password + "';"
    sql_perms = "GRANT ALL PRIVILEGES ON " + task_name.lower() + ".* TO '" + task_name.lower() + "';"

    try:
        with db1.cursor() as cursor:
            cursor.execute(sql_db)
            cursor.execute(sql_user)
            cursor.execute(sql_perms)
    finally:
        db1.close()

    write_vault_path = settings["VAULT_PROJECT_NAME"] + "/" + task_name.lower() + "/" + environment.lower() + "/"

    print("[DEBUG] Writing Secret " + write_vault_path + "mysql_pw")

    vault_client.write(write_vault_path + "mysql_pw", value=db_user_password)

# ------------------
