from sqlmodel import SQLModel, create_engine, Session
from .config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if "sqlite" in settings.assemble_db_connection else {}

engine = create_engine(
    settings.assemble_db_connection, 
    echo=False, 
    connect_args=connect_args
)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)
