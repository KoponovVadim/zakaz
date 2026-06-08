from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User


def main() -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == settings.admin_email))
        if user:
            print(f"Admin already exists: {settings.admin_email}")
            return
        db.add(
            User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                role="admin",
                is_active=True,
            )
        )
        db.commit()
        print(f"Admin created: {settings.admin_email}")


if __name__ == "__main__":
    main()
