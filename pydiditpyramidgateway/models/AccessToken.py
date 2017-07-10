from datetime import datetime
from string import letters
from string import digits
from string import punctuation
from Crypto.Random import random
from base64 import b64encode
from base64 import b64decode
from hashlib import pbkdf2_hmac

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey

from sqlalchemy.orm import relation
from sqlalchemy.orm import backref

import pydiditpyramidgateway.models.meta
from pydiditpyramidgateway.models.User import User

from sqlalchemy.orm.exc import NoResultFound


# We use : as a divider in the token, so remove it here
punctuation = punctuation.translate(None, ':')
token_characters = letters + digits + punctuation

Base = pydiditpyramidgateway.models.meta.Base

salt_length = 16


class AccessToken(Base):
    '''AccessToken object'''
    __tablename__ = 'access_tokens'

    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
        primary_key=True
    )
    token_hash = Column(Unicode(length=80), nullable=False)
    created_at = Column(DateTime(), nullable=False, default=datetime.now)

    user = relation(
        'User',
        backref=backref('access_tokens')
    )

    def __init__(self, **kwargs):
        '''Create a new AccessToken instance

        '''
        super(AccessToken, self).__init__(**kwargs)

        # Not part of Model, so not put into persistent storage
        self.token = ''.join(
            [random.choice(token_characters) for i in xrange(1024)]
        ).encode('utf-8')

        salt = ''.join(
            [random.choice(token_characters) for i in xrange(salt_length)]
        ).encode('utf-8')

        self.token_hash = b64encode(pbkdf2_hmac(
            'sha256',
            self.token,
            salt,
            100000
        )).decode('utf-8')
        self.token_hash += salt

    def __str__(self):
        return '<AccessToken: User {0}>'.format(self.user_id)

    def __repr__(self):
        return str(self)

    def encode_for_client(self):
        # : cannot be in the decoded token's right hand side
        return {'access_token': b64encode('{0}:{1}'.format(
            self.user.username,
            self.token
        ))}

    @staticmethod
    def verify_access_token(dbsession, encoded_token):
        try:
            decoded_token = b64decode(encoded_token)
        except TypeError:
            return None

        username, submitted_access_token = decoded_token.split(':')

        try:
            known_access_token_instance = dbsession.query(AccessToken) \
                                                   .join(User) \
                                                   .filter(
                User.username==username.decode('utf-8')
            ).one()
        except NoResultFound:
            return None

        decoded_known_hash = b64decode(
            known_access_token_instance.token_hash[:-salt_length]
                                       .encode('utf-8')
        )
        salt = known_access_token_instance.token_hash[-salt_length:] \
                                          .encode('utf-8')

        submitted_hash = pbkdf2_hmac(
            'sha256',
            submitted_access_token,
            salt,
            100000
        )

        if submitted_hash == decoded_known_hash:
            return known_access_token_instance.user.id

        return None
