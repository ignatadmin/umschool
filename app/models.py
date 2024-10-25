from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
Base = declarative_base()


class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    scores = relationship("Score", back_populates="student")

class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    scores = relationship("Score", back_populates="subject")

class Score(Base):
    __tablename__ = 'scores'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    score = Column(Integer, nullable=False)
    student = relationship("Student", back_populates="scores")
    subject = relationship("Subject", back_populates="scores")

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
