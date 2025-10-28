# db_init.py
import os
from models import init_db, create_user

if __name__ == "__main__":
    # Ensure upload directories exist for proctoring artifacts
    os.makedirs("uploads/proctor_images", exist_ok=True)

    init_db()
    # create default accounts (ignore if already exist)
    try:
        create_user("admin", "adminpass", is_admin=1)
    except Exception:
        pass
    try:
        create_user("student", "studentpass", is_admin=0)
    except Exception:
        pass
    print("DB initialized with admin/student (admin/adminpass, student/studentpass)")
