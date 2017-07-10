def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('trade_for_client_credentials', '/trade')
    config.add_route('pass_to_backend', '/api/{function_name}')
