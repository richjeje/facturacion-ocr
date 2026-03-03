from passlib.context import CryptContext
from backend.core.database import SessionLocal
from backend.core.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

try:
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        admin.hashed_password = pwd_context.hash("admin123")
        db.commit()
        print("Password for 'admin' reset to 'admin123'")
    else:
        # Create admin if it doesn't exist
        new_admin = User(
            username="admin",
            hashed_password=pwd_context.hash("admin123"),
            email="admin@mistica.com",
            role="admin",
            status="active"
        )
        db.add(new_admin)
        db.commit()
        print("Admin user created with password 'admin123'")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
