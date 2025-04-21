from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.utils.logger import get_logger

# Get logger
logger = get_logger("db")

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# # Add event listeners for SQL execution
# @event.listens_for(engine, "before_cursor_execute")
# def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
#     conn.info.setdefault('query_start_time', []).append(event.TimestampCollector())
#     logger.debug(f"Executing query: {statement}")

# @event.listens_for(engine, "after_cursor_execute")
# def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
#     total = conn.info['query_start_time'].pop(-1).total
#     logger.debug(f"Query completed in {total:.4f}s")


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    