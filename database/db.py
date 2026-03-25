import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "tuition.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ── Engine & SessionFactory ────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


# ── Helpers ────────────────────────────────────────────────────────────────────
def get_db() -> Session:
    """Return a raw session (caller must close)."""
    return SessionLocal()


@contextmanager
def db_session():
    """Context-manager session with automatic commit / rollback."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Create all tables if they don't already exist."""
    from database.models import Base  # local import to avoid circular refs
    Base.metadata.create_all(bind=engine)