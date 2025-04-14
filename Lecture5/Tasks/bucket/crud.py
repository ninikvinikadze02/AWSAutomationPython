from botocore.exceptions import ClientError
import os 


def create_bucket(aws_s3_client, bucket_name, region) -> bool:
    location = {'LocationConstraint': region}
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/create_bucket.html
    response = aws_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration=location
    )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        return True
    return False


def delete_bucket(aws_s3_client, bucket_name) -> bool:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/delete_bucket.html
    response = aws_s3_client.delete_bucket(Bucket=bucket_name)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 204:
        return True
    return False


def bucket_exists(aws_s3_client, bucket_name) -> bool:
    try:
        response = aws_s3_client.head_bucket(Bucket=bucket_name)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if status_code == 200:
            return True
    except ClientError:
        # print(e)
        return False

def configure_static_website_hosting(aws_s3_client, bucket_name):
    # Define the website configuration
    aws_s3_client.delete_public_access_block(Bucket=bucket_name)
    print("Delete public access block for the s3 bucket")
    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }
    aws_s3_client.put_bucket_website(Bucket=bucket_name,
                      WebsiteConfiguration=website_configuration)

    result = aws_s3_client.get_bucket_website(Bucket=bucket_name)
    if result["ResponseMetadata"]["HTTPStatusCode"] == 200:
        return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        os.getenv("aws_s3_region_name"),
        bucket_name,
        "index.html"
    )
    else:
        return result
