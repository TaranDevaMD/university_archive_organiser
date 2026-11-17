# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # "admin" or "faculty"
    
    subjects = relationship("Subject", back_populates="faculty")

class AcademicYear(Base):
    __tablename__ = "academic_years"
    
    id = Column(Integer, primary_key=True, index=True)
    year_range = Column(String, unique=True, nullable=False) # e.g., "2023-2024"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    subjects = relationship("Subject", back_populates="academic_year", cascade="all, delete")

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    regulation = Column(String, nullable=False)
    course_type = Column(String, nullable=False) # Major, Minor, Value-added
    course_format = Column(String, nullable=False) # Theory, Practical, etc.
    year_no = Column(Integer, nullable=False) # 1, 2, 3, or 4
    semester_no = Column(Integer, nullable=False) # 1 to 8
    
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    academic_year = relationship("AcademicYear", back_populates="subjects")
    faculty = relationship("User", back_populates="subjects")
    files = relationship("FileVersion", back_populates="subject", cascade="all, delete")

class FileVersion(Base):
    __tablename__ = "file_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    subfolder_name = Column(String, nullable=False) # namelist, cia 1, midsem, etc.
    file_name = Column(String, nullable=False)
    version_number = Column(Integer, default=1, nullable=False)
    onedrive_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    subject = relationship("Subject", back_populates="files")