import boto3
from botocore.exceptions import ClientError

from app.config import settings


def get_s3_client():
    """Get configured S3 client."""
    return boto3.client(
        "s3",
        use_ssl=False,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        endpoint_url=settings.s3_endpoint_url,
    )


def check_s3_connection() -> bool:
    """Check if S3 connection and bucket access is working."""
    try:
        s3_client = get_s3_client()
        s3_client.head_bucket(Bucket=settings.s3_bucket_name)
        return True
    except ClientError:
        return False
