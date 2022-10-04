from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, ForeignKey, Column, Integer, String, Boolean
from sqlalchemy.orm import relationship


db = SQLAlchemy()


connection = Table(
    'connection',
    db.Model.metadata,
    Column('from_user', String, ForeignKey('User.username')),
    Column('to_user', String, ForeignKey('User.username'))
)


class User(db.Model):
    __tablename__ = 'User'

    username = Column(String(32), primary_key=True)
    password = Column(String(128), nullable=False)
    is_active = Column(Boolean)

    connects = relationship(
        'User',
        secondary=connection,
        primaryjoin=username == connection.c.from_user,
        secondaryjoin=username == connection.c.to_user,
        backref='from'
    )

    def __repr__(self):
        return f'<User> {self.username}'
