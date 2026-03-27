from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from ..core.messages import get_error


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)

    @model_validator(mode="after")
    def _validate_password_complexity(self) -> "RegisterRequest":
        """パスワードに英大文字・英小文字・数字をそれぞれ1文字以上含むことを検証する。"""
        p = self.password
        if not any(c.isupper() for c in p):
            raise ValueError(get_error("validation.password_uppercase"))
        if not any(c.islower() for c in p):
            raise ValueError(get_error("validation.password_lowercase"))
        if not any(c.isdigit() for c in p):
            raise ValueError(get_error("validation.password_digit"))
        return self


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
