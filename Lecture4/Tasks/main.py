import logging
from botocore.exceptions import ClientError
from auth import init_client
from bucket.crud import list_buckets, create_bucket, delete_bucket, bucket_exists
from object.crud import upload_local_file
from my_args import bucket_arguments, object_arguments
import argparse

parser = argparse.ArgumentParser(
    description="CLI program that helps with S3 buckets.",
    prog='main.py',
    epilog='DEMO APP - 2 FOR BTU_AWS'
)

subparsers = parser.add_subparsers(dest='command')

bucket = bucket_arguments(subparsers.add_parser("bucket", help="work with Bucket/s"))
object = object_arguments(subparsers.add_parser("object", help="work with Object/s"))


def main():
    s3_client = init_client()
    args = parser.parse_args()

    match args.command:

        case "bucket":
            if args.create_bucket == "True":
                if (args.bucket_check == "True") and bucket_exists(s3_client, args.name):
                    parser.error("Bucket already exists")
                if create_bucket(s3_client, args.name, args.region):
                    print(f"Bucket: '{args.name}' successfully created")

            if (args.delete_bucket == "True") and delete_bucket(s3_client, args.name):
                print("Bucket successfully deleted")

        case "object":
            if args.local_object:
                print(upload_local_file(s3_client, args.bucket_name, args.local_object, args.keep_file_name, args.upload_type))


if __name__ == "__main__":
    try:
        main()
    except ClientError as error:
        if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            logging.warning("Bucket already exists! Using it.")
        else:
            logging.error(error)
    except ValueError as error:
        logging.error(error)
