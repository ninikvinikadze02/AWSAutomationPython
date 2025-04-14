from datetime import datetime, timedelta, timezone
def list_object_versions(aws_s3_client, bucket_name, file_name):
    versions = aws_s3_client.list_object_versions(
        Bucket=bucket_name,
        Prefix=file_name
    )
    list_of_versions = []
    for version in versions['Versions']:
        version_id = version['VersionId']
        file_key = version['Key'],
        is_latest = version['IsLatest']
        modified_at = version['LastModified']
        list_of_versions.append((version_id, file_key, is_latest, modified_at))
        print(version_id, file_key, is_latest, modified_at)
    return list_of_versions

def delete_versions_older_than_six_months(aws_s3_client_name, bucket_name, file_name):
    versions = list_object_versions(aws_s3_client_name, bucket_name, file_name)
    for version in versions:
        if version[3] < datetime.now(timezone.utc) - timedelta(days=180):
            aws_s3_client_name.delete_object(
                Bucket=bucket_name,
                Key=version[1][0],
                VersionId=version[0]
            )
            print(f"{file_name} version {version[0]} deleted successfully!")