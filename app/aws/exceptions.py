class S3UploadError(Exception):
    """Raised when S3 file upload fails."""

    pass


class S3DownloadError(Exception):
    """Raised when S3 file download fails."""

    pass


class S3DeleteError(Exception):
    """Raised when S3 file deletion fails."""

    pass


class S3ConnectionError(Exception):
    """Raised when S3 connection fails."""

    pass
