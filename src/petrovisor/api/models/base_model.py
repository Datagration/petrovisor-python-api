from pydantic import (
    BaseModel,
    ConfigDict,
)


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
