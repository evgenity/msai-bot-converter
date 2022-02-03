import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import close_all_sessions
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///bot-converter.db', echo=True)
Base = declarative_base()


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    filename = Column(String)

    def __repr__(self):
        return "<File(chat_id='{}', filename='{}')>".format(self.chat_id, self.filename)
    

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    username = Column(String)
    state = Column(String)

    def __repr__(self):
        return "<User(chat_id='{}', username='{}')>".format(self.chat_id, self.filename)


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

ed_file = File(chat_id=0, filename='test.mov')
ed_user = User(chat_id=0, username='admin')

session.add(ed_file)
session.add(ed_user)

session.commit()
