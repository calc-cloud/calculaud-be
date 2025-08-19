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
    auth_jwks_url: str
    auth_issuer: str
    auth_audience: str | None = None
    auth_algorithm: Annotated[str, Field(default="RS256")]
    auth_token_endpoint_url: str
    auth_oidc_url: str

    # OAuth2 Client Configuration (for Swagger UI authorization)
    oauth_client_id: str | None = None
    oauth_scopes: Annotated[str, Field(default="openid")]

    # AI Configuration (Universal LLM support)
    llm_base_url: Annotated[str, Field(default="https://api.openai.com/v1")]
    llm_api_key: Annotated[str, Field(default="")]
    model_name: Annotated[str, Field(default="gpt-4o")]
    mcp_server_url: Annotated[str, Field(default="http://localhost:8000/mcp")]

    model_config = SettingsConfigDict(
        env_file=".test.env" if os.getenv("TESTING") else find_dotenv(),
        extra="ignore",  # Ignore unknown environment variables during migration
    )


settings = Settings()
