import os
from urllib.request import urlopen
import io
from hashlib import md5
from time import localtime
from io import BytesIO


def get_objects(aws_s3_client, bucket_name) -> str:
    for key in aws_s3_client.list_objects(Bucket=bucket_name)['Contents']:
        print(f" {key['Key']}, size: {key['Size']}")


def delete_object(aws_s3_client, bucket_name, key):
    try:
        result = aws_s3_client.delete_object(Bucket=bucket_name, Key=key)
        print(f"Object {key} deleted")
        return result
    except Exception as e:
        print(f"Error: {e}")


def download_file_and_upload_to_s3(aws_s3_client,
                                   bucket_name,
                                   url,
                                   keep_local=False) -> str:
    file_name = f'image_file_{md5(str(localtime()).encode("utf-8")).hexdigest()}.jpg'
    with urlopen(url) as response:
        content = response.read()
        aws_s3_client.upload_fileobj(Fileobj=io.BytesIO(content),
                                     Bucket=bucket_name,
                                     ExtraArgs={'ContentType': 'image/jpg'},
                                     Key=file_name)
    if keep_local:
        with open(file_name, mode='wb') as jpg_file:
            jpg_file.write(content)

    # public URL
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format('us-west-2',
                                                         bucket_name, file_name)


def upload_file(aws_s3_client, filename, bucket_name):
    try:
        response = aws_s3_client.upload_file(filename, bucket_name, "hello.txt")
        return "Successfully uploaded"
    except Exception as e:
        return f"Error: {e}"


def upload_file_obj(aws_s3_client, filename, bucket_name):
    with open(filename, "rb") as file:
        aws_s3_client.upload_fileobj(file, bucket_name, "hello_obj.txt")


def upload_file_put(aws_s3_client, filename, bucket_name):
    with open(filename, "rb") as file:
        aws_s3_client.put_object(Bucket=bucket_name,
                                 Key="hello_put.txt",
                                 Body=file.read())


def multipart_upload(aws_s3_client, filename, bucket_name):
    mpu = aws_s3_client.create_multipart_upload(Bucket=bucket_name, Key=filename)
    mpu_id = mpu['UploadId']
    parts = []
    uploaded_bytes = 0
    total_bytes = os.stat(filename).st_size
    with open(filename, "rb") as f:
        i = 1
        while True:
            data = f.read(1024 * 10)
            if not len(data):
                break
            part = aws_s3_client.upload_part(Bucket=bucket_name,
                                             Key=filename,
                                             PartNumber=i,
                                             UploadId=mpu_id,
                                             Body=data)
            parts.append({"PartNumber": i, "ETag": part["ETag"]})
            uploaded_bytes += len(data)
            print(f"Uploaded: {uploaded_bytes}/{total_bytes}")
            i += 1
    result = aws_s3_client.complete_multipart_upload(Bucket=bucket_name,
                                                     Key=filename,
                                                     UploadId=mpu_id,
                                                     MultipartUpload={"Parts": parts})
    print(result)
    return result


def list_object_versioning(aws_s3_client, bucket_name, key):
    # Fetch all versions for the specific key
    versions = []
    response = aws_s3_client.list_object_versions(Bucket=bucket_name, Prefix=key)

    # Filter only the versions that match the exact key
    if 'Versions' in response:
        versions.extend([v for v in response['Versions'] if v['Key'] == key])

    # Handle pagination if necessary
    while response.get('IsTruncated'):
        response = aws_s3_client.list_object_versions(
            Bucket=bucket_name,
            Prefix=key,
            KeyMarker=response.get('NextKeyMarker'),
            VersionIdMarker=response.get('NextVersionIdMarker')
        )
        if 'Versions' in response:
            versions.extend([v for v in response['Versions'] if v['Key'] == key])
    # Print the total count and version details
    print(f"Total versions for '{key}': {len(versions)}")
    for version in versions:
        print(
            f"VersionId: {version['VersionId']}, LastModified: {version['LastModified']}, IsLatest: {version['IsLatest']}")


def rollback_to_previous_version(aws_s3_client, bucket_name: str, object_key: str):
    # Step 1: Get all versions for the object key
    versions = []
    response = aws_s3_client.list_object_versions(Bucket=bucket_name, Prefix=object_key)

    # Filter for only matching key versions
    if 'Versions' in response:
        versions.extend([v for v in response['Versions'] if v['Key'] == object_key])

    # Paginate if necessary
    while response.get('IsTruncated'):
        response = aws_s3_client.list_object_versions(
            Bucket=bucket_name,
            Prefix=object_key,
            KeyMarker=response.get('NextKeyMarker'),
            VersionIdMarker=response.get('NextVersionIdMarker')
        )
        if 'Versions' in response:
            versions.extend([v for v in response['Versions'] if v['Key'] == object_key])

    # Step 2: Sort by LastModified (latest first)
    versions.sort(key=lambda v: v['LastModified'], reverse=True)

    if len(versions) < 2:
        print("Not enough versions to rollback.")
        return

    # Step 3: Get the second latest version
    previous_version = versions[1]  # index 1 is the version before the latest
    version_id = previous_version['VersionId']

    # Step 4: Download the previous version
    obj = aws_s3_client.get_object(Bucket=bucket_name, Key=object_key, VersionId=version_id)
    data = obj['Body'].read()

    # Step 5: Re-upload the previous version to make it the latest
    aws_s3_client.upload_fileobj(Fileobj=BytesIO(data), Bucket=bucket_name, Key=object_key)
    print(f"Rolled back '{object_key}' to version ID: {version_id} (now latest)")