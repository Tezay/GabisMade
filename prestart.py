import os
from app import create_app, db


def ensure_db_initialized():
    app = create_app()
    with app.app_context():
        instance_dir = app.instance_path
        db_path = os.path.join(instance_dir, 'site.db')
        os.makedirs(instance_dir, exist_ok=True)

        # Always attempt to create all tables; this is idempotent.
        print(f"[prestart] Ensuring database and schema at {db_path}")
        db.create_all()
        print("[prestart] Database schema ensured (create_all executed)")


if __name__ == "__main__":
    ensure_db_initialized()
