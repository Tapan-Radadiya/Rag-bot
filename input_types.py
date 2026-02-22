from pydantic import BaseModel


class NewUserBase(BaseModel):
    user_email: str


class AllUserData(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class TextEmbedding(BaseModel):
    user_text: str


class UserQue(BaseModel):
    user_text: str


class EmbeddingsResponse(BaseModel):
    text: str
    similarity: float

    class Config:
        from_attributes = True
