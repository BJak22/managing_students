from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import base


class Student(base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(32))
    surname = Column(String(32))
    email = Column(String(64))

    # Relationship with Document
    documents = relationship('Document', back_populates='student')


class Document(base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id'))  # Foreign Key setup
    doc_name = Column(String(64))