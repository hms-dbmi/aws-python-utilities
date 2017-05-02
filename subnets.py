from netaddr import *
import time


def create_subnet_and_tags(vpc, subnet, name_tag, availability_zone):

    subnet = vpc.create_subnet(CidrBlock=subnet, AvailabilityZone=availability_zone)

    time.sleep(5)

    subnet.create_tags(Tags=[{'Key': 'Name', 'Value': name_tag}])


def create_db_subnets(vpc, stack_name, settings):

    print("Creating CIDR blocks.")
    ip = IPNetwork(settings["CIDR_BLOCK_START"])
    subnets = list(ip.subnet(28))

    # One Availability zone needs to be from settings, the other needs to be in a different one.
    print("Creating DB Subnets.")
    create_subnet_and_tags(vpc, str(subnets[0]), stack_name + "_DB_1", settings["AVAILABILITY_ZONE"])
    create_subnet_and_tags(vpc, str(subnets[1]), stack_name + "_DB_2", "us-east-1b")
