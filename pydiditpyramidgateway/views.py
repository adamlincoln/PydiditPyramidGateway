import pydiditbackend

import simplejson as json

from pyramid.view import view_config


def _stringify(thing):
    if hasattr(thing, '__iter__'):
        if hasattr(thing, 'keys'):
            return dict([(key, _stringify(value)) for key, value in thing.iteritems()])
        else:
            return [_stringify(element) for element in thing]
    else:
        if thing.__class__.__name__ == 'datetime':
            return thing.isoformat()
        else:
            return thing


@view_config(route_name='home', renderer='json')
def home(request):
    f = request.params['f']
    args = json.loads(request.params['args'])
    kwargs = json.loads(request.params['kwargs'])
    to_return = _stringify(getattr(pydiditbackend, f)(*args, **kwargs))
    pydiditbackend.commit()
    return to_return
