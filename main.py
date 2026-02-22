from typing import Annotated
from fastapi import FastAPI, Depends, status
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from input_types import NewUserBase, AllUserData, TextEmbedding, EmbeddingsResponse
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer
from sqlalchemy.sql import text
from sqlalchemy import select
from transformers import pipeline

app = FastAPI()

model = SentenceTransformer("all-MiniLM-L6-v2")

pipe = pipeline("text-classification", model="google/gemma-3-1b-it")


def create_db_and_tables():
    models.Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/")
def test_route():
    print("hello World")
    return {"Hello": "World"}


@app.post("/new-user")
async def insert_user(new_user: NewUserBase, db: db_dependency):
    print("=====", new_user.user_email)
    result = (
        db.query(models.UserData)
        .filter(models.UserData.email == new_user.user_email)
        .first()
    )
    if result:
        return JSONResponse(
            {"message": "User Already Exists"}, status_code=status.HTTP_409_CONFLICT
        )
    db_newuser = models.UserData(email=new_user.user_email)
    db.add(db_newuser)
    db.commit()
    return JSONResponse(
        {"Success": "User Entered Successfully"}, status_code=status.HTTP_201_CREATED
    )


@app.get("/get-all-user", response_model=list[AllUserData])
async def get_all_user(db: db_dependency):
    result = db.query(models.UserData).all()
    print("result", result)
    return result


@app.post("/get-embeddings")
async def get_text_embeddings(user_text_input: TextEmbedding, db: db_dependency):
    embeddings = generateEmbeddings(user_text_input.user_text)
    new_embeddings = models.Document(
        embedding=embeddings,
        text=user_text_input.user_text,
    )
    db.add(new_embeddings)
    db.commit()
    return {"Data": "data"}


@app.post("/ask-prompt", response_model=list[EmbeddingsResponse])
def ask_prompt(db: db_dependency, user_que: TextEmbedding):
    embeddings = generateEmbeddings(user_que.user_text)

    distance = models.Document.embedding.cosine_distance(embeddings)
    similarity = (1 - distance).label("similarity")

    raw_query = select(models.Document.text, similarity).order_by(distance).limit(3)

    data = db.execute(raw_query).all()
    print("data", data)
    return data


def generateEmbeddings(user_text: str):
    embeddings = model.encode(user_text)
    return embeddings
