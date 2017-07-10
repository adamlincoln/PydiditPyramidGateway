import os
import sys
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from pydiditpyramidgateway.models.meta import Base
from pydiditpyramidgateway.models import (
    get_engine,
    get_session_factory,
    get_tm_session,
    )
from pydiditpyramidgateway.models.User import User
from pydiditpyramidgateway.models.InitialToken import InitialToken

from pydiditpyramidgateway.views.default import remove_access_tokens


def usage(argv):
    cmd = os.path.basename(argv[0])
    print 'usage: {0} <config_uri> new_user_name\n' \
          '(example: "{0} development.ini yourname")'.format(cmd)
    sys.exit()


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    username = argv[2]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)

    engine = get_engine(settings)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(engine)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        user = None
        script_name = os.path.basename(argv[0])
        if script_name == 'create_new_user':
            user = User(username.decode('utf-8'))
            dbsession.add(user)
            try:
                dbsession.flush()
            except IntegrityError as e:
                if 'UNIQUE' in e.message:
                    print '{0} is not a unique username.  ' \
                          'Please choose another.'.format(username)
                    transaction.abort()
                    sys.exit(1)
                raise e
        elif script_name == 'make_initial_token':
            try:
                user = dbsession.query(User).filter_by(username=username).one()
            except NoResultFound:
                print '{0} is not a valid username.'.format(username)
                sys.exit(1)

            for token in user.initial_tokens:
                dbsession.delete(token)

        remove_access_tokens(dbsession, user.id)

        initial_token = InitialToken(user)
        dbsession.add(initial_token)

        print 'Initial token for {0}: {1}'.format(
            user.username,
            initial_token.token
        )
