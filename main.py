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
from fastapi.responses import StreamingResponse
import json
import requests

app = FastAPI()

model = SentenceTransformer("all-MiniLM-L6-v2")


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


@app.post("/ask-prompt", response_model=list[str])
def ask_prompt(db: db_dependency, user_que: TextEmbedding):
    embeddings = generateEmbeddings(user_que.user_text)

    distance = models.Document.embedding.cosine_distance(embeddings)

    raw_query = select(models.Document.text).order_by(distance).limit(3)

    data = db.execute(raw_query).scalars().all()
    response = StreamingResponse(askLocalLLM(user_que.user_text, data))

    return response


def askLocalLLM(text: str, localContext: str):
    formated_prompt = (
        f"""You are a question-answering assistant.

You must answer the user's question using ONLY the information provided in the CONTEXT section below.

Rules:

1. Use only the provided context to answer.
2. Do NOT use your own knowledge or assumptions.
3. If the answer is not explicitly present in the context, respond exactly with:
   "I don't know based on the provided context."
4. Do NOT guess.
5. Do NOT add external facts.
6. Keep the answer concise and factual.

CONTEXT:
{localContext}

QUESTION:
{text}

ANSWER:"""
        ""
    )
    print(formated_prompt)
    response = requests.post(
        "http://192.168.1.31:11434/api/generate",
        json={
            "model": "phi3",
            "prompt": formated_prompt,
            "stream": True,
        },
        stream=True,
    )

    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode("utf-8"))
            token = chunk.get("response", "")
            print(token)
            yield token
            if chunk.get("done"):
                break


def generateEmbeddings(user_text: str):
    embeddings = model.encode(user_text)
    return embeddings
