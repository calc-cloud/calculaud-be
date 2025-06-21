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

    # API
    api_v1_prefix: Annotated[str, Field(default="/api/v1")]

    # Pagination
    default_page_size: Annotated[int, Field(default=20)]
    max_page_size: Annotated[int, Field(default=100)]

    model_config = SettingsConfigDict(env_file=find_dotenv())


settings = Settings()  # type: ignore
