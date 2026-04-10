from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    username: str
    is_github_user: bool = False


class UserResponse(BaseModel):
    username: str
    email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GitHubCallbackRequest(BaseModel):
    code: str = Field(min_length=1)
    state: str = Field(min_length=1)
