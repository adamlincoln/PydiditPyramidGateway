from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import DateTime

import pydiditpyramidgateway.models.meta

Base = pydiditpyramidgateway.models.meta.Base


class User(Base):
    '''User object'''
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    username = Column(Unicode(length=255), nullable=False, unique=True)
    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    modified_at = Column(
        DateTime(),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    def __init__(self, username):
        '''Create a new User instance

        :param username:

        '''
        self.username = username

    def __str__(self):
        return '<User: {0}>'.format(self.id, self.username)

    def __repr__(self):
        return str(self)
