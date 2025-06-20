import argparse
from auth import aws_client
from vpc import get_or_create_vpc, get_or_set_igw, create_route_table_without_route, create_subnet, associate_route_table_to_subnet, create_route_table_with_route, enable_auto_public_ips
from ec2 import create_key_pair, create_security_group, add_ssh_access_sg, run_ec2
from rds import create_db_subnet_group, create_rds_security_group, create_db_instance


def main():
    parser = argparse.ArgumentParser(description="Create AWS infrastructure.")
    parser.add_argument('--vpc_name_tag', required=True, help='Name tag for the VPC.')
    parser.add_argument('--route_name', required=True, help='Name for the route table and route.')
    parser.add_argument('--ec2_instance_name', required=True, help='Name for the EC2 instance.')
    parser.add_argument('--security_group_name', required=True, help='Name for the security group.')
    args = parser.parse_args()

    client = aws_client('ec2')

    vpc_id = get_or_create_vpc(client, args.vpc_name_tag) # Using a default CIDR block if creating

    get_or_set_igw(client, vpc_id)

    private_subnets = []
    # create private subnet
    subnet_id = create_subnet(client, vpc_id, '10.0.0.0/24', 'private_sub_1', 'us-east-1a')
    rtb_id = create_route_table_without_route(client, vpc_id)
    associate_route_table_to_subnet(client, rtb_id, subnet_id)
    private_subnets.append(subnet_id)
    subnet_id = create_subnet(client, vpc_id, '10.0.1.0/24', 'private_sub_2','us-east-1b')
    rtb_id = create_route_table_without_route(client, vpc_id)
    associate_route_table_to_subnet(client, rtb_id, subnet_id)
    private_subnets.append(subnet_id)
    print(f'private subnets : {private_subnets}')
    # public subnet
    subnet_id = create_subnet(client, vpc_id, '10.0.2.0/24', 'public_sub_1',
                                'us-east-1a')
    rtb_id = create_route_table_with_route(client, vpc_id, args.route_name,
        get_or_set_igw(client, vpc_id))
    associate_route_table_to_subnet(client, rtb_id, subnet_id)
    enable_auto_public_ips(client, subnet_id, 'enable')

    # create key pair
    create_key_pair(client, "my-demo-key")

    # create ec2 sg_id
    ec2_security_group_id = create_security_group(
    client, args.security_group_name, "Security group to enable access on ec2", vpc_id)

    # only concrete ip rule
    add_ssh_access_sg(client, ec2_security_group_id)

    # EC2
    run_ec2(client, ec2_security_group_id, subnet_id, args.ec2_instance_name)

    # RDS - Postgres
    rds_client = aws_client('rds')

    security_group_name = f"{args.security_group_name}-rds"

    # SG for RDS

    rds_subnet_group = create_db_subnet_group(rds_client, security_group_name,
                                                vpc_id, private_subnets)
    print("switched to ec2")
    rds_sg_id = create_rds_security_group(aws_client('ec2'), security_group_name,
                                            vpc_id, ec2_security_group_id)
    
    create_db_instance(rds_client, rds_sg_id, rds_subnet_group)


if __name__ == '__main__':
  main()
