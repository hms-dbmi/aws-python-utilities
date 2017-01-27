from netaddr import *
import time


def create_subnet_and_tags(vpc, subnet, name_tag):

    subnet = vpc.create_subnet(CidrBlock=subnet)

    time.sleep(5)

    subnet.create_tags(Tags=[{'Key': 'Name', 'Value': name_tag}])


def create_db_subnets(vpc, stack_name, cidr_block_start):

    print("Creating CIDR blocks.")
    ip = IPNetwork(cidr_block_start)
    subnets = list(ip.subnet(28))

    print("Creating DB Subnets.")
    create_subnet_and_tags(vpc, str(subnets[0]), stack_name + "_DB_1")
    create_subnet_and_tags(vpc, str(subnets[1]), stack_name + "_DB_2")