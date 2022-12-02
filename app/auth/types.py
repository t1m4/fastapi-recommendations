from pydantic import BaseModel, Field


class User(BaseModel):
    id: int = Field(...)
    email: str = Field(default="")
    company_id: int = Field(default="")
    is_authenticated: bool = Field(default=True)
    first_name: str = Field(default="")
    last_name: str = Field(default="")
    has_financial_access: bool = Field(default=False)


class AuthUser(BaseModel):
    """User object from authentication service"""

    id: int
    role: str | None
    email: str
    first_name: str
    last_name: str
    company_id: int


class Company(BaseModel):
    id: int
    name: str


class AuthUsers(BaseModel):
    __root__: list[AuthUser]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]


class AuthPlatform(BaseModel):
    recommendation_id: int
    channel_name: str
    platform_name: str
    email: str
