import uuid
from typing import BinaryIO

from botocore.exceptions import ClientError

from app.aws.client import get_s3_client
from app.config import settings


class S3Service:
    def __init__(self):
        self.s3_client = get_s3_client()
        self.bucket_name = settings.s3_bucket_name
        self.key_prefix = settings.s3_key_prefix

    def upload_file(self, file_obj: BinaryIO, original_filename: str) -> str:
        """
        Upload file to S3 and return the S3 key.

        Args:
            file_obj: File-like object to upload
            original_filename: Original filename for extension preservation

        Returns:
            S3 key of uploaded file

        Raises:
            ClientError: If upload fails
        """
        # Generate unique key with original extension
        file_extension = ""
        if "." in original_filename:
            file_extension = "." + original_filename.split(".")[-1].lower()

        s3_key = f"{self.key_prefix}{uuid.uuid4()}{file_extension}"

        try:
            # Add content disposition header with original filename
            extra_args = {
                "ContentDisposition": f'attachment; filename="{original_filename}"'
            }
            self.s3_client.upload_fileobj(
                file_obj, self.bucket_name, s3_key, ExtraArgs=extra_args
            )
            return s3_key
        except ClientError as e:
            raise e

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for file download.

        Args:
            s3_key: S3 key of the file
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL for download

        Raises:
            ClientError: If presigned URL generation fails
        """
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            raise e

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3.

        Args:
            s3_key: S3 key of the file to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            s3_key: S3 key to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False


s3_service = S3Service()
