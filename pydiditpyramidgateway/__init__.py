from pyramid.config import Configurator
from pyramid.renderers import JSON

from pydiditpyramidgateway.policies import MixedTokenAuthenticationPolicy
from pydiditpyramidgateway.policies import AlwaysPassAuthenticatedAuthorizationPolicy

import pydiditbackend

from datetime import datetime


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    json_renderer = JSON()

    def datetime_adapter(obj, request):
        return obj.isoformat()

    json_renderer.add_adapter(datetime, datetime_adapter)
    config.add_renderer('json', json_renderer)

    config.include('pyramid_jinja2')
    config.include('.models')
    config.include('.routes')
    config.set_authentication_policy(MixedTokenAuthenticationPolicy())
    config.set_authorization_policy(
        AlwaysPassAuthenticatedAuthorizationPolicy()
    )

    enabled_registration_modules = settings.get(
        'pydiditpyramidgateway.enabled_registration_modules'
    )
    if enabled_registration_modules is not None:
        enabled_registration_modules = config.maybe_dotted(
            enabled_registration_modules.split(',')
        )
        for module in enabled_registration_modules:
            config.include(module)

    config.scan()
    pydiditbackend.initialize()
    return config.make_wsgi_app()
