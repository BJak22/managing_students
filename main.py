from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
import secrets
import models
from database import engine, sessionLocal
from sqlalchemy.orm import Session
import os
from typing import List, Optional, Annotated
import shutil
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasicCredentials, HTTPBasic
import boto3

#AWS S3 Configuration
s3_bucket = os.getenv('S3_BUCKET', 'bjak22studentmanagement')
s3_region = os.getenv('S3_REGION', ' us-east-1')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID', 'AKIAYM7PN65OF55HABN6')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', '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')
s3_client = boto3.client(
    's3',
    region_name=s3_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

app = FastAPI()
models.base.metadata.create_all(bind=engine)
security = HTTPBasic()

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

#verify credentials
def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"admin"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.username.encode("utf8")
    correct_password_bytes = b"admin"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def verify_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"admin"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.username.encode("utf8")
    correct_password_bytes = b"admin"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        return False
    return True

@app.get("/users/me")
def read_current_user(username: Annotated[str, Depends(get_current_username)]):
    return {"username": username}

@app.get("/")
def root():
    return {"Welcome in Student Management API"}

@app.post("/students/", response_model=Student)
def create_student(student: StudentCreate, db: Session = Depends(get_db),
                   credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@app.put("/students/update/{student_id}", response_model=Student)
def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(get_db),
                   credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials):
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
    if not verify_credentials(credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if db_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    db.query(models.Student).filter(models.Student.id == student_id).delete()
    db.commit()
    return {"message": "Student deleted"}


@app.get("/students/", response_model=List[Student])
def get_students(db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return db.query(models.Student).all()

#managing pdfs
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/students/{student_id}/upload-pdf/")
async def upload_pdf(student_id: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only PDFs are allowed.")
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    existing_document = db.query(models.Document).filter_by(doc_name=file.filename).first()
    if existing_document:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="A file with this name already exists")
    max_size_mb = int(os.getenv("MAX_PDF_SIZE_MB", 5))
    if file.size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds limit.")

    s3_key = f"uploads/{file.filename}"
    s3_client.upload_fileobj(file.file, s3_bucket, s3_key, ExtraArgs={"ContentType": "application/pdf"})

    db_document = models.Document(student_id=student_id, doc_name=file.filename)
    db.add(db_document)
    db.commit()

    return {"filename": file.filename, "student_id": student_id}


@app.get("/get_pdf/{student_id}/{filename}")
async def get_pdf(student_id: int, filename: str, db: Session = Depends(get_db),
                  credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    try:
        db_document = db.query(models.Document).filter_by(student_id=student_id, doc_name=filename).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Document not found")

    # Pobieranie pliku PDF z S3
    s3_key = f"uploads/{filename}"
    s3_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': s3_bucket, 'Key': s3_key}, ExpiresIn=3600)

    return {"url": s3_url}


@app.delete("/delete_pdf/")
async def delete_pdf(student_id: int, filename: str, db: Session = Depends(get_db),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not verify_credentials(credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    try:
        db_document = db.query(models.Document).filter_by(student_id=student_id, doc_name=filename).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Document not found in the database")

    # Usuń plik z S3
    s3_key = f"uploads/{filename}"
    s3_client.delete_object(Bucket=s3_bucket, Key=s3_key)

    db.delete(db_document)
    db.commit()

    return {"detail": "File and database entry deleted successfully"}

#seeds
def add_seeds(db: Session):
    students = [
        models.Student(
            name="John",
            surname="Doe",
            email="john.doe@example.com",
            field="Computer Science",
            documents=[
            ]
        ),
        models.Student(
            name="Jane",
            surname="Smith",
            email="jane.smith@example.com",
            field="Mathematics",
            documents=[
            ]
        ),
        models.Student(
            name="Jan",
            surname="Kowalski",
            email="JanK@example.com",
            field="Computer Science",
            documents=[
            ]
        ),
        models.Student(
            name="Maria",
            surname="Nowak",
            email="MNowak@example.com",
            field="Mathematics",
            documents=[
            ]
        ),
        models.Student(
            name="Wiktor",
            surname="Malinowski",
            email="Malina_wik@example.com",
            field="Physics",
            documents=[
            ]
        ),
        models.Student(
            name="Sarah",
            surname="Johnson",
            email="Sohnson@example.com",
            field="Computer Science",
            documents=[
            ]
        ),
        models.Student(
            name="Jan",
            surname="Dabrowski",
            email="JanDabrowski@example.com",
            field="Computer Science",
            documents=[
            ]
        ),
        models.Student(
            name="Andrzej",
            surname="Grochowski",
            email="a.grochowski@example.com",
            field="Mathematics",
            documents=[
            ]
        ),
        models.Student(
            name="Tom",
            surname="McCartan",
            email="McTom@example.com",
            field="Physics",
            documents=[
        ]
        ),
        models.Student(
            name="Zygmunt",
            surname="Waza",
            email="zigi3@example.com",
            field="Physics",
            documents=[
        ]
        ),
        models.Student(
            name="Michael",
            surname="Brown",
            email="michael.brown@example.com",
            field="Physics",
            documents=[
            ]
        ),
        models.Student(
            name="Emily",
            surname="Johnson",
            email="emily.johnson@example.com",
            field="Biology",
            documents=[
            ]
        ),
        models.Student(
            name="William",
            surname="Davis",
            email="william.davis@example.com",
            field="Chemistry",
            documents=[
            ]
        ),
        models.Student(
            name="Olivia",
            surname="Martinez",
            email="olivia.martinez@example.com",
            field="Psychology",
            documents=[
            ]
        ),
        models.Student(
            name="James",
            surname="Wilson",
            email="james.wilson@example.com",
            field="Engineering",
            documents=[
            ]
        ),
        models.Student(
            name="Sophia",
            surname="Garcia",
            email="sophia.garcia@example.com",
            field="Architecture",
            documents=[
            ]
        ),
        models.Student(
            name="Henry",
            surname="Miller",
            email="henry.miller@example.com",
            field="Literature",
            documents=[
            ]
        ),
        models.Student(
            name="Ava",
            surname="Taylor",
            email="ava.taylor@example.com",
            field="Economics",
            documents=[
            ]
        ),
    ]

    db.add_all(students)
    db.commit()

def seed_database():
    db = sessionLocal()
    seed = int(os.getenv("SEED", 0))
    if seed == 1:
        try:
            add_seeds(db)
        finally:
            db.close()

seed_database()

