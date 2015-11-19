__author__ = 'wangdai'

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from jrcms import APP


if __name__ == '__main__':
    # APP.run(debug=True)
    http_server = HTTPServer(WSGIContainer(APP))
    http_server.listen(5000)
    IOLoop.instance().start()
