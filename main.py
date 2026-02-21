from typing import Annotated
from fastapi import FastAPI, Depends, status
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from input_types import NewUserBase, AllUserData
from fastapi.responses import JSONResponse

app = FastAPI()


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
