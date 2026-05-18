from pydantic import BaseModel, EmailStr, Field


class ContactRequest(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    subject: str = Field(min_length=2)
    message: str = Field(min_length=10)

