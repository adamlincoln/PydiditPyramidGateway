from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey

from sqlalchemy.orm import relation
from sqlalchemy.orm import backref

import pydiditpyramidgateway.models.meta
from pydiditpyramidgateway.models.User import User

from xkcdpass import xkcd_password


short_token_wordlist = xkcd_password.generate_wordlist()

Base = pydiditpyramidgateway.models.meta.Base


class InitialToken(Base):
    '''InitialToken object'''
    __tablename__ = 'initial_tokens'

    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
        primary_key=True
    )
    token = Column(Unicode(length=255), nullable=False)
    created_at = Column(DateTime(), nullable=False, default=datetime.now)

    user = relation(
        'User',
        backref=backref('initial_tokens')
    )

    def __init__(self, user):
        '''Create a new InitialToken instance

        '''
        if isinstance(user, User):
            user = user.id

        self.user_id = user
        self.token = xkcd_password.generate_xkcdpassword(
            short_token_wordlist,
            numwords=2
        ).decode('utf-8')

    def __str__(self):
        return '<InitialToken: User {0}>'.format(self.user_id)

    def __repr__(self):
        return str(self)
