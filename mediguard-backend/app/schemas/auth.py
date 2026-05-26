from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str | None = None
    username: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Accept either a URL reset token OR the 6-digit OTP code sent in the email."""
    token: str | None = None
    otp_code: str | None = Field(None, min_length=6, max_length=6, pattern=r"^\d{6}$")
    password: str = Field(min_length=6)

    @model_validator(mode="after")
    def token_or_code_required(self) -> "ResetPasswordRequest":
        if not self.token and not self.otp_code:
            raise ValueError("Either 'token' (from reset link) or 'otp_code' (6-digit code) must be provided.")
        return self


class PatchNotificationRequest(BaseModel):
    notify_emails: bool


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)

