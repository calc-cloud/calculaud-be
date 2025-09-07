import os
from typing import Annotated

from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: Annotated[str, Field(default="sqlite:///./app.db")]

    # App
    app_name: Annotated[str, Field(default="Procurement Management System")]
    debug: Annotated[bool, Field(default=False)]
    version: Annotated[str, Field(default="1.0.0")]
    environment: Annotated[str, Field(default="development")]

    # API
    api_v1_prefix: Annotated[str, Field(default="/api/v1")]
    root_path: Annotated[
        str, Field(default="")
    ]  # For reverse proxy path prefix (e.g., "/staging")

    # Pagination
    default_page_size: Annotated[int, Field(default=100)]
    max_page_size: Annotated[int, Field(default=200)]

    # AWS S3 Configuration
    aws_access_key_id: Annotated[str, Field(default="")]
    aws_secret_access_key: Annotated[str, Field(default="")]
    aws_region: Annotated[str | None, Field(default=None)]
    s3_endpoint_url: Annotated[str | None, Field(default=None)]
    s3_use_ssl: Annotated[bool, Field(default=True)]
    s3_bucket_name: Annotated[str, Field(default="calculaud-files")]
    s3_bucket_url: Annotated[str, Field(default="")]
    s3_key_prefix: Annotated[str, Field(default="files/")]
    s3_storage_class: Annotated[str | None, Field(default=None)]

    # File Upload Configuration
    max_file_size_mb: Annotated[int, Field(default=1024)]  # 1GB in MB

    # Currency Configuration
    usd_to_ils_rate: Annotated[float, Field(default=3.7)]

    # Authentication Configuration
    auth_oidc_url: str  # OIDC discovery URL (.well-known/openid-configuration)
    auth_audience: str | None = None

    # Role-based access control
    required_role: Annotated[str, Field(default="calUsers")]
    role_claim_path: Annotated[str, Field(default="role")]

    # OAuth2 Client Configuration (for Swagger UI authorization)
    oauth_client_id: str | None = None
    oauth_scopes: Annotated[str, Field(default="openid")]

    model_config = SettingsConfigDict(
        env_file=".test.env" if os.getenv("TESTING") else find_dotenv()
    )


settings = Settings()  # type: ignore
