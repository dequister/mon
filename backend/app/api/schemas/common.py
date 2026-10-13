from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """DTO base: converte entidades ORM em respostas JSON."""

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    detail: str
