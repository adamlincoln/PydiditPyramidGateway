import pydiditbackend

import simplejson as json
from datetime import datetime

from pyramid.view import view_config

import logging
log = logging.getLogger(__name__)

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


@view_config(route_name='home', renderer='string')
def home(request):
    f = request.params['f']
    if f.startswith('_'): # Enforce hidden functions
        return ''
    args = json.loads(request.params['args'], object_hook=_decode_datetime)
    kwargs = json.loads(request.params['kwargs'], object_hook=_decode_datetime)
    to_return = json.dumps(getattr(pydiditbackend, f)(*args, **kwargs), default=_encode_datetime)
    pydiditbackend.commit()
    return to_return
