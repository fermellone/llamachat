from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from llamachat.config import AppConfig

engine = create_engine(AppConfig.database_url)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session 