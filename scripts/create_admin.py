"""
Run this to create the first admin user:
python scripts/create_admin.py
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.models import User

Base.metadata.create_all(bind=engine)

def create_admin():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first():
            print("Admin user already exists")
            return
        admin = User(
            username="admin", email="admin@gmail.com",
            first_name="System", last_name="Admin",
            role="admin", password=hash_password("password@123"), is_active=True
        )
        db.add(admin)
        db.commit()
        print("Admin created — username: admin  password: password@123")
        print("Change the password immediately after first login!")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
