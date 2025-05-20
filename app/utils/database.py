from sqlalchemy import create_engine
from app.utils.singleton import singleton
from sqlalchemy.orm import sessionmaker
from app.config import Settings

@singleton
class Database():
    def __init__(self) -> None:
        engine = create_engine(Settings.DATABASE_URL, echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def get_session(self):
        return self.session