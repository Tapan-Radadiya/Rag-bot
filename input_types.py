from pydantic import BaseModel


class NewUserBase(BaseModel):
    user_email: str


class AllUserData(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True
