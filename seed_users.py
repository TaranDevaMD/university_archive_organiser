# seed_users.py (Debug Version)
import sys

print("DEBUG: Script has started running!")

try:
    from database import SessionLocal
    import models
    print("DEBUG: Successfully imported database and models!")
    
    from passlib.context import CryptContext
    print("DEBUG: Successfully imported passlib!")
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    print("DEBUG: CryptContext created successfully!")

    db = SessionLocal()
    print("DEBUG: Database session opened successfully!")
    
    # Check if admin exists
    existing_admin = db.query(models.User).filter(models.User.username == "admin").first()
    if existing_admin:
        print("Users already seeded in the database!")
    else:
        admin_password = pwd_context.hash("admin123")
        admin_user = models.User(username="admin", password_hash=admin_password, role="admin")
        
        faculty_password = pwd_context.hash("faculty123")
        faculty_user = models.User(username="prof_smith", password_hash=faculty_password, role="faculty")
        
        db.add(admin_user)
        db.add(faculty_user)
        db.commit()
        print("DEFAULT ADMIN AND FACULTY CREATED SUCCESSFULLY!")
        
    db.close()
    print("DEBUG: Script finished successfully!")

except Exception as e:
    print(f"CRITICAL ERROR ENCOUNTERED: {e}")

sys.stdout.flush()