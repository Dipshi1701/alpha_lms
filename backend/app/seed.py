from app import config
from app.database import SessionLocal
from app.models import Role, User
from app.security import hash_password, ROLE_NAMES


def seed_database():
    """Create default roles and admin user on first startup."""
    db = SessionLocal()
    try:
        # Create the three roles if they don't exist yet
        for name in ROLE_NAMES:
            if not db.query(Role).filter(Role.name == name).first():
                db.add(Role(name=name))
        db.commit()

        # Create the admin user if it doesn't exist yet
        email = config.ADMIN_EMAIL.strip().lower()
        if not db.query(User).filter(User.email == email).first():
            admin_role = db.query(Role).filter(Role.name == "Administrator").first()
            admin = User(
                email=email,
                hashed_password=hash_password(config.ADMIN_PASSWORD),
                full_name="Administrator",
                is_active=True,
            )
            admin.roles.append(admin_role)
            db.add(admin)
            db.commit()
    finally:
        db.close()
