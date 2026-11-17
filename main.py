# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
import models
from database import SessionLocal, engine
from pathlib import Path
import shutil
from typing import List
from fastapi import UploadFile, File, Form

# 1. Initialize FastAPI app FIRST so routes can use it
app = FastAPI(title="Academic Department EDMS")

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define where local folders will be stored (acts as our local drive before OneDrive)
STORAGE_ROOT = Path("department_storage")

# Dependency to get database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC SCHEMES (DATA BLUEPRINTS) ---

class LoginRequest(BaseModel):
    username: str
    password: str

class SubjectInput(BaseModel):
    name: str
    regulation: str
    course_type: str      # "major", "minor", "value-added"
    course_format: str    # "theory", "practical", "theory-cum-practical"
    year_no: int          # 1, 2, 3, or 4
    semester_no: int      # 1 to 8
    faculty_id: int       # Which faculty member is in charge

class AcademicYearCreateRequest(BaseModel):
    year_range: str       # e.g., "2023-2024"
    subjects: List[SubjectInput]


# --- API ROUTES ---

@app.post("/api/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # 1. Find user in the database by username
    user = db.query(models.User).filter(models.User.username == request.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # 2. Verify the password against the stored hash
    if not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # 3. Return user details and role
    return {
        "message": "Login successful",
        "username": user.username,
        "role": user.role
    }


@app.post("/api/admin/create-academic-year")
def create_academic_year(data: AcademicYearCreateRequest, db: Session = Depends(get_db)):
    # Step 1: Check if academic year already exists in database
    existing_year = db.query(models.AcademicYear).filter(models.AcademicYear.year_range == data.year_range).first()
    if existing_year:
        raise HTTPException(status_code=400, detail="This Academic Year already exists!")

    # Step 2: Save the new Academic Year to the database
    new_academic_year = models.AcademicYear(year_range=data.year_range)
    db.add(new_academic_year)
    db.commit()
    db.refresh(new_academic_year)

    # Step 3: Automatically generate physical folders on disk
    year_folder_path = STORAGE_ROOT / data.year_range
    standard_subfolders = ["namelist", "course files", "cia 1", "midsem", "cia 2", "endsem"]
    created_subjects_info = []

    for subj in data.subjects:
        # Save subject to database
        db_subject = models.Subject(
            name=subj.name,
            regulation=subj.regulation,
            course_type=subj.course_type,
            course_format=subj.course_format,
            year_no=subj.year_no,
            semester_no=subj.semester_no,
            academic_year_id=new_academic_year.id,
            faculty_id=subj.faculty_id
        )
        db.add(db_subject)
        db.commit()
        db.refresh(db_subject)

        # Build physical folder path for this subject
        subject_dir = year_folder_path / f"Year_{subj.year_no}" / f"Semester_{subj.semester_no}" / subj.name
        
        # Create standard subfolders inside the subject directory
        for sub_name in standard_subfolders:
            target_sub = subject_dir / sub_name
            target_sub.mkdir(parents=True, exist_ok=True)

        # Regulation Cloning Logic (Fixed parenthesis bug here!)
        old_subject_with_same_reg = db.query(models.Subject).filter(
            models.Subject.regulation == subj.regulation,
            models.Subject.name == subj.name,
            models.Subject.id != db_subject.id
        ).first()

        if old_subject_with_same_reg:
            old_ac_year = db.query(models.AcademicYear).filter(models.AcademicYear.id == old_subject_with_same_reg.academic_year_id).first()
            if old_ac_year:
                old_subject_dir = STORAGE_ROOT / old_ac_year.year_range / f"Year_{subj.year_no}" / f"Semester_{subj.semester_no}" / subj.name
                if old_subject_dir.exists():
                    for item in old_subject_dir.iterdir():
                        if item.is_dir():
                            dest_sub = subject_dir / item.name
                            dest_sub.mkdir(parents=True, exist_ok=True)
                            for file_item in item.iterdir():
                                if file_item.is_file():
                                    shutil.copy(file_item, dest_sub / file_item.name)

        created_subjects_info.append(subj.name)

    return {
        "message": f"Academic Year {data.year_range} created successfully with folder automation!",
        "subjects_created": created_subjects_info
    }


# --- FACULTY ROUTES ---

@app.get("/api/faculty/subjects/{faculty_id}")
def get_faculty_subjects(faculty_id: int, db: Session = Depends(get_db)):
    """
    Returns only the subjects assigned to this specific faculty member,
    used to populate frontend dropdowns securely.
    """
    subjects = db.query(models.Subject).filter(models.Subject.faculty_id == faculty_id).all()
    
    if not subjects:
        return {"message": "No subjects assigned to this faculty member.", "subjects": []}
    
    subject_list = []
    for subj in subjects:
        # Find the academic year text
        ac_year = db.query(models.AcademicYear).filter(models.AcademicYear.id == subj.academic_year_id).first()
        subject_list.append({
            "subject_id": subj.id,
            "name": subj.name,
            "regulation": subj.regulation,
            "year_no": subj.year_no,
            "semester_no": subj.semester_no,
            "academic_year": ac_year.year_range if ac_year else "Unknown"
        })
        
    return {"subjects": subject_list}


@app.post("/api/faculty/upload-file")
async def upload_file(
    subject_id: int = Form(...),
    subfolder_name: str = Form(...), # e.g., "cia 1", "namelist"
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Handles faculty file uploads with security checks and automated versioning.
    """
    # 1. Verify the subject exists and get its details
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found!")

    ac_year = db.query(models.AcademicYear).filter(models.AcademicYear.id == subject.academic_year_id).first()
    if not ac_year:
        raise HTTPException(status_code=404, detail="Academic year not found for this subject!")

    # 2. Construct the target physical directory path
    target_dir = STORAGE_ROOT / ac_year.year_range / f"Year_{subject.year_no}" / f"Semester_{subject.semester_no}" / subject.name / subfolder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    original_filename = file.filename
    
    # 3. Version Control Logic: Check if a file with this name already exists in database
    existing_file_record = db.query(models.FileVersion).filter(
        models.FileVersion.subject_id == subject_id,
        models.FileVersion.subfolder_name == subfolder_name,
        models.FileVersion.file_name == original_filename
    ).order_by(models.FileVersion.version_number.desc()).first()

    next_version = 1
    if existing_file_record:
        next_version = existing_file_record.version_number + 1

    # 4. Modify file name to include version tracking if version > 1
    # e.g., "Report.pdf" -> "Report_v2.pdf"
    file_stem = Path(original_filename).stem
    file_suffix = Path(original_filename).suffix
    versioned_filename = f"{file_stem}_v{next_version}{file_suffix}" if next_version > 1 else original_filename

    file_path = target_dir / versioned_filename

    # 5. Save the physical file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 6. Save metadata record to database
    db_file_version = models.FileVersion(
        subject_id=subject_id,
        subfolder_name=subfolder_name,
        file_name=original_filename,
        version_number=next_version,
        onedrive_path=str(file_path)
    )
    db.add(db_file_version)
    db.commit()

    return {
        "message": f"File uploaded successfully as Version {next_version}!",
        "filename": versioned_filename,
        "version": next_version,
        "path": str(file_path)
    }