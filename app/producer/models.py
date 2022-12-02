from pydantic import BaseModel


class URLSchemaEndpoint(BaseModel):
    path: str
    features: list[str]
    is_regex: bool = True
    post_for_read: bool = False


class URLSchema(BaseModel):
    service: str
    endpoints: list[URLSchemaEndpoint]
