from urllib.request import urlopen
import io
from hashlib import md5
from time import localtime
from os import getenv, stat
import magic
from pathlib import Path


def get_objects(aws_s3_client, bucket_name) -> str:
    for key in aws_s3_client.list_objects(Bucket=bucket_name)['Contents']:
        print(f" {key['Key']}, size: {key['Size']}")


def generate_file_name(file_extension) -> str:
    return f'up_{md5(str(localtime()).encode("utf-8")).hexdigest()}.{file_extension}'


def upload_local_file(aws_s3_client, bucket_name, filename, keep_file_name, upload_type="upload_file"):
    (s3_region := getenv("aws_s3_region_name", "us-west-2"))

    file_path = Path(f"static/{filename}")
    mime_type = magic.from_file(file_path, mime=True)
    content_type = mime_type
    file_name = filename
    folder_name = None

    if not content_type:
        raise ValueError("Invalid type")
    else:
        folder_name = file_name.split(".")[-1]

    if upload_type == "upload_file":
        aws_s3_client.upload_file(
            Filename=file_path,
            Bucket=bucket_name,
            Key=f"{folder_name}/{file_name}" if folder_name else file_name,
            ExtraArgs={'ContentType': content_type}
        )
    elif upload_type == "upload_fileobj":
        with open(file_path, "rb") as file:
            aws_s3_client.upload_fileobj(
                Fileobj=file,
                Bucket=bucket_name,
                Key=f"{folder_name}/{file_name}" if folder_name else file_name,
                ExtraArgs={'ContentType': content_type}
            )
    elif upload_type == "put_object":
        with open(file_path, "rb") as file:
            aws_s3_client.put_object(
                Body=file.read(),
                Bucket=bucket_name,
                Key=f"{folder_name}/{file_name}" if folder_name else file_name,
                ExtraArgs={'ContentType': content_type}
            )

    # public URL
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        s3_region,
        bucket_name,
        f"{folder_name}/{file_name}" if folder_name else file_name
    )
