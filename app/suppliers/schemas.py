from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.files.schemas import FileAttachmentResponse


class SupplierBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    file_icon_id: int | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]
    file_icon_id: int | None = None


class Supplier(SupplierBase):
    id: int
    file_icon: FileAttachmentResponse | None = None

    model_config = ConfigDict(from_attributes=True)
