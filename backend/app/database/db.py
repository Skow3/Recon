from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from ..config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        with engine.begin() as conn:
            if "cases" in table_names:
                case_cols = [c["name"] for c in inspector.get_columns("cases")]
                if "workspace_id" not in case_cols:
                    conn.execute(text("ALTER TABLE cases ADD COLUMN workspace_id VARCHAR DEFAULT 'ws_finance'"))
                if "workflow_id" not in case_cols:
                    conn.execute(text("ALTER TABLE cases ADD COLUMN workflow_id VARCHAR DEFAULT 'wf_billing_investigator'"))
            if "tool_runs" in table_names:
                tr_cols = [c["name"] for c in inspector.get_columns("tool_runs")]
                if "workspace_id" not in tr_cols:
                    conn.execute(text("ALTER TABLE tool_runs ADD COLUMN workspace_id VARCHAR"))
                if "workflow_id" not in tr_cols:
                    conn.execute(text("ALTER TABLE tool_runs ADD COLUMN workflow_id VARCHAR"))
            if "audit_logs" in table_names:
                al_cols = [c["name"] for c in inspector.get_columns("audit_logs")]
                if "workspace_id" not in al_cols:
                    conn.execute(text("ALTER TABLE audit_logs ADD COLUMN workspace_id VARCHAR"))
                if "workflow_id" not in al_cols:
                    conn.execute(text("ALTER TABLE audit_logs ADD COLUMN workflow_id VARCHAR"))
    except Exception as e:
        print(f"Column migration notice: {e}")

