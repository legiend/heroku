# -*- coding: utf-8 -*-
import os
from werkzeug.wsgi import SharedDataMiddleware
from portfolio import Portfolio
from settings import *

def create_app():
    app = Portfolio({
        'redis_host': redis_set["redis_host"],
        'redis_port': redis_set["redis_port"]
    })
    if with_static:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')
        })
    return app

if __name__ == "__main__":
	from werkzeug.serving import run_simple
	app = create_app()
	run_simple(host, port, app, use_debugger, use_reloader)#run server