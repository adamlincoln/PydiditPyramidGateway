from zope.interface import implementer

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.security import Everyone
from pyramid.security import Authenticated

from sqlalchemy.orm.exc import NoResultFound

from pydiditpyramidgateway.models.User import User
from pydiditpyramidgateway.models.InitialToken import InitialToken
from pydiditpyramidgateway.models.AccessToken import AccessToken


class AlwaysPassAuthenticatedAuthorizationPolicy(object):
    '''Authorization is enforced by the real pydidit backend.'''
    def permits(self, context, principals, permission):
        return permission in principals

    def principals_allowed_by_permission(self, context, permission):
        raise NotImplementedError()


@implementer(IAuthenticationPolicy)
class MixedTokenAuthenticationPolicy(object):
    def get_trade_payload(self, request):
        try:
            payload = request.json_body
        except ValueError:
            return None

        if not isinstance(payload, dict) or \
           len(payload) != 2 or \
           'username' not in payload or \
           'initial_token' not in payload:
            return None

        return payload

    def authenticated_userid(self, request):
        """ Return the authenticated :term:`userid` or ``None`` if
        no authenticated userid can be found. This method of the
        policy should ensure that a record exists in whatever
        persistent store is used related to the user (the user
        should not have been deleted); if a record associated with
        the current id does not exist in a persistent store, it
        should return ``None``.

        """
        def cache(request, return_value, is_trade):
            request.cached_authenticated_userid = (return_value, is_trade)
            return request.cached_authenticated_userid

        # We cache the result in the request because the trade logic is not
        # idempotent.
        if hasattr(request, 'cached_authenticated_userid'):
            return request.cached_authenticated_userid

        if request.matched_route.name == 'trade_for_client_credentials':
            payload = self.get_trade_payload(request)

            if request.registry.settings.get(
                'pydiditpyramidgateway.authentication_off'
            ) == 'true':
                try:
                    user = request.dbsession.query(User) \
                                  .filter_by(username=payload['username']) \
                                  .one()
                except NoResultFound:
                    return cache(request, None, True)

                return cache(request, user.id, True)

            # query for initial token
            # right now, the DB constrains to just one initial token per user,
            # but we'll be more generic here.
            initial_tokens = request.dbsession.query(InitialToken).join(User) \
                                    .filter(
                                        User.username==payload['username']
                                    ).all()

            user_id = None
            for initial_token in initial_tokens:
                if initial_token.token == payload['initial_token']:
                    user_id = initial_token.user_id
                    # Don't break, because we want to keep deleting

                # always delete any initial token for the requested username
                request.dbsession.delete(initial_token)

            if user_id is None:
                return cache(request, None, True)

            return cache(request, user_id, True)
        else:
            if 'authorization' not in request.headers:
                return cache(request, None, False)
            authorization_header = request.headers['authorization']
            header_components = authorization_header.split()
            if len(header_components) != 2 or \
               header_components[0].upper() != 'BEARER':
                return cache(request, None, False)

            submitted_access_token = header_components[1]

            user_id = AccessToken.verify_access_token(
                request.dbsession,
                submitted_access_token
            )

            return cache(request, user_id, False)

    def unauthenticated_userid(self, request):
        """ Return the *unauthenticated* userid.  This method
        performs the same duty as ``authenticated_userid`` but is
        permitted to return the userid based only on data present
        in the request; it needn't (and shouldn't) check any
        persistent store to ensure that the user record related to
        the request userid exists.

        This method is intended primarily a helper to assist the
        ``authenticated_userid`` method in pulling credentials out
        of the request data, abstracting away the specific headers,
        query strings, etc that are used to authenticate the request.

        """
        raise NotImplementedError()

    def effective_principals(self, request):
        """ Return a sequence representing the effective principals
        typically including the :term:`userid` and any groups belonged
        to by the current user, always including 'system' groups such
        as ``pyramid.security.Everyone`` and
        ``pyramid.security.Authenticated``.

        """
        principals = [Everyone]

        user_id, was_trade = self.authenticated_userid(request)

        if user_id is None:
            return principals

        if was_trade:
            principals += ['AuthenticatedForTrade', str(user_id)]
        else:
            principals += [Authenticated, str(user_id)]

        return principals

    def remember(self, request, userid, **kw):
        """ Return a set of headers suitable for 'remembering' the
        :term:`userid` named ``userid`` when set in a response.  An
        individual authentication policy and its consumers can
        decide on the composition and meaning of **kw.

        """
        raise NotImplementedError()

    def forget(self, request):
        """ Return a set of headers suitable for 'forgetting' the
        current user on subsequent requests.

        """
        raise NotImplementedError()


@implementer(IAuthenticationPolicy)
class DumbAuthenticationPolicy(CallbackAuthenticationPolicy):
    def get_trade_payload(self, request):
        try:
            payload = request.json_body
        except ValueError:
            return None

        if not isinstance(payload, dict) or \
           len(payload) != 2 or \
           'username' not in payload or \
           'initial_token' not in payload:
            return None

        return payload

    def callback(self, uid, request):
        # Just pass trade requests - we'll check the initial token in the view
        if request.matched_route.name == 'trade_for_client_credentials' and \
           request.method == 'POST':
            return []

        return None

    def unauthenticated_userid(self, request):
        payload = self.get_trade_payload(request)
        if payload is None:
            return None

        try:
            user = request.dbsession.query(User) \
                          .filter_by(username=payload['username']).one()
        except NoResultFound:
            return None

        return user.id

    def remember(self, request, principal, **kw):
        raise NotImplementedError()

    def forget(self, request):
        raise NotImplementedError()
