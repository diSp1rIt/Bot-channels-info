from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import Integer, String, DateTime
from .db_session import SqlAlchemyBase


class Channel(SqlAlchemyBase):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    pts = Column(Integer)
    participants_count = Column(Integer)
    pinned_msg_id = Column(Integer, nullable=True)
    record_date = Column(DateTime, default=datetime.now)


class Post(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, index=True)
    channel_id = Column(Integer, index=True)
    message = Column(String, default='')
    views = Column(Integer)
    post_date = Column(DateTime)
    record_date = Column(DateTime, default=datetime.now)

