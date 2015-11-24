#!/usr/bin/env python
__author__ = 'wangdai'

import logging
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from jrcms import APP


if __name__ == '__main__':
    # APP.run(debug=True)
    access_log = logging.getLogger('tornado.access')
    access_log.setLevel(logging.INFO)
    http_server = HTTPServer(WSGIContainer(APP), xheaders=True)
    http_server.listen(5000, address='127.0.0.1')
    IOLoop.instance().start()
