from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    question: Annotated[
        str, Field(min_length=1, max_length=5000, description="User question")
    ]

    model_config = ConfigDict(from_attributes=True)


class AskResponse(BaseModel):
    answer: Annotated[str, Field(description="AI response to the user question")]

    model_config = ConfigDict(from_attributes=True)
