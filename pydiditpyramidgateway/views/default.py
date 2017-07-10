from pyramid.view import view_config
from pyramid.security import Authenticated

from pyramid.httpexceptions import exception_response

from pydiditpyramidgateway.models.AccessToken import AccessToken
from pydiditpyramidgateway.models.User import User

import simplejson as json
from datetime import datetime

import pydiditbackend


def remove_access_tokens(dbsession, authenticated_userid):
    # Blow away existing tokens
    for access_token in dbsession.query(AccessToken) \
                                 .filter_by(
                                     user_id=authenticated_userid
                                 ):
        dbsession.delete(access_token)


def make_access_token(request):
    auid = request.authenticated_userid[0]

    remove_access_tokens(request.dbsession, auid)

    new_access_token = AccessToken(
        user=request.dbsession.query(User).filter_by(id=auid).one()
    )
    request.dbsession.add(new_access_token)
    return new_access_token


allowed_calls = {
    'initialize': False,
    'get': True,
    'get_new_lowest_display_position': True,
    'put': True,
    'commit': True,
    'flush': True,
    'delete_from_db': True,
    'set_completed': True,
    'set_attributes': True,
    'swap_display_positions': True,
    'relationship_name': True,
    'link': True,
    'unlink': True,
    'move': True,
    'search': True,
    'get_users': True,
    'get_workspaces': True,
    'create_user': True,
    'create_workspace': True,
    'give_permission': True,
    'revoke_permission': True,
}


def _encode_datetime(v):
    if hasattr(v, 'isoformat'):
        return v.isoformat()
    raise TypeError


def _decode_datetime(initial_result):
    for k, v in initial_result.iteritems():
        if isinstance(v, basestring):
            try:
                dt = datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                pass
            else:
                initial_result[k] = dt
    return initial_result


@view_config(route_name='pass_to_backend', renderer='json',
             permission=Authenticated)
def pass_to_backend_view(request):
    f = request.matchdict['function_name']

    if f not in allowed_calls:
        raise exception_response(400)

    try:
        payload = request.json_body
    except ValueError:
        return None

    args = json.loads(
        payload.get('args', '[]'),
        object_hook=_decode_datetime
    )
    kwargs = json.loads(
        payload.get('kwargs', '{}'),
        object_hook=_decode_datetime
    )

    to_return = None  # Will get set either way
    if f in allowed_calls and allowed_calls[f]:
        try:
            to_return = json.dumps(
                getattr(pydiditbackend, f)(*args, **kwargs),
                default=_encode_datetime
            )
        except TypeError:
            import sys
            import traceback
            print sys.exc_info()
            print traceback.format_exc()
            raise exception_response(400)
    else:
        raise exception_response(400)
    return to_return


@view_config(route_name='trade_for_client_credentials', renderer='json',
             permission='AuthenticatedForTrade')
def trade_for_client_credentials_view(request):
    return make_access_token(request).encode_for_client()
