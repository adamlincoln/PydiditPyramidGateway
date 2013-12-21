from pyramid.config import Configurator

from pydiditbackend import initialize


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    initialize()
    config.scan()
    return config.make_wsgi_app()
