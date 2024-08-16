from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound

import models
from database import engine, sessionLocal
from sqlalchemy.orm import Session
import os
from typing import List, Optional
import shutil
from fastapi.responses import FileResponse

#verify credentials
from fastapi.security import HTTPBasicCredentials, HTTPBasic

def verify_credentials(credentials: HTTPBasicCredentials, db: Session) -> bool:
    # Implement your authentication logic here.
    return True

app = FastAPI()
models.base.metadata.create_all(bind=engine)

class DocumentBase(BaseModel):
    student_id: int
    doc_name: str

class StudentBase(BaseModel):
    name: str
    surname: str
    email: str
    field: str
    documents: Optional[List[DocumentBase]] = []

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class Student(StudentBase):
    id: int

class Config:
    orm_mode = True

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"test"}

security = HTTPBasic

@app.post("/students/", response_model=Student)
def create_student(student: StudentCreate, db: Session = Depends(get_db),
                   credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@app.put("/students/update/{student_id}", response_model=Student)
def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(get_db),
                   credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if db_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if db_student:
        for key, value in student.dict().items():
            setattr(db_student, key, value)
        db.commit()
        db.refresh(db_student)
        return db_student


@app.delete("/students/del/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db),
                   credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if db_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    db.query(models.Student).filter(models.Student.id == student_id).delete()
    db.commit()
    return {"message": "Student deleted"}


@app.get("/students/", response_model=List[Student])
def get_students(db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return db.query(models.Student).all()

#managing pdfs
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/students/{student_id}/upload-pdf/")
async def upload_pdf(student_id: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only PDFs are allowed.")
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    max_size_mb = int(os.getenv("MAX_PDF_SIZE_MB", 5))
    if file.size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds limit.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_document = models.Document(student_id=student_id, doc_name=file.filename)
    db.add(db_document)
    db.commit()

    return {"filename": file.filename, "student_id": student_id}


@app.get("/get_pdf/{student_id}/{filename}")
async def get_pdf(student_id: int, filename: str, db: Session = Depends(get_db),
                  credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    try:
        db_document = db.query(models.Document).filter_by(student_id=student_id, doc_name=filename).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type='application/pdf', filename=filename)


@app.delete("/delete_pdf/")
async def delete_pdf(student_id: int, filename: str, db: Session = Depends(get_db),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        db_document = db.query(models.Document).filter_by(student_id=student_id, doc_name=filename).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Document not found in the database")

    os.remove(file_path)

    db.delete(db_document)
    db.commit()

    return {"detail": "File and database entry deleted successfully"}
