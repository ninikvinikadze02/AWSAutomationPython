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

    allowed_types = {
        "jpeg": "image/jpeg",
        "png": "image/png",
        "mp4": "video/mp4",
        "txt": "text/plain",
        "html": "text/html"
    }

    file_path = Path(f"static/{filename}")
    mime_type = magic.from_file(file_path, mime=True)
    content_type = None
    file_name = None

    for type, ctype in allowed_types.items():
        if mime_type == ctype:
            content_type = ctype
            file_name = filename if keep_file_name else generate_file_name(type)

    if not content_type:
        raise ValueError("Invalid type")

    if upload_type == "upload_file":
        aws_s3_client.upload_file(
            file_path,
            bucket_name,
            file_name,
            ExtraArgs={'ContentType': content_type}
        )
    elif upload_type == "upload_fileobj":
        with open(file_path, "rb") as file:
            aws_s3_client.upload_fileobj(
                file,
                bucket_name,
                file_name,
                ExtraArgs={'ContentType': content_type}
            )
    elif upload_type == "put_object":
        with open(file_path, "rb") as file:
            aws_s3_client.put_object(
                Body=file.read(),
                Bucket=bucket_name,
                Key=file_name,
                ExtraArgs={'ContentType': content_type}
            )
    elif upload_type == "multipart_upload":
        multipart_upload(
            aws_s3_client,
            bucket_name,
            file_path,
            file_name,
            content_type
        )

    # public URL
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        s3_region,
        bucket_name,
        file_name
    )