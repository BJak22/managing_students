from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, sessionLocal
from sqlalchemy.orm import Session



app = FastAPI()
models.base.metadata.create_all(bind=engine)

class StudentBase(BaseModel):
    name: str
    surname: str
    email: str

class DocumentBase(BaseModel):
    student_id: int
    doc_name: str

def get_db():
    db = sessionLocal
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/")
def root():
    return {"test"}

@app.post("/students", status_code=status.HTTP_201_CREATED)
async def create_student(student:StudentBase, db:db_dependency):
    db_studnet = models.Student(**student.dict())
    db.add(student)
    db.commit()
