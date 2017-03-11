import importlib
from collections import OrderedDict
import logging

import tornado.web
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AsyncIOMainLoop
from Coronado.Plugin import AppPlugin as AppPluginBase

from .RequestHandler import RequestHandler
from .WebSocketHandler import WebSocketHandler

logger = logging.getLogger(__name__)

# Default config
config = \
{
    'allowedCORSOrigins': [],
    'allowedWSOrigins': [],
    'apiVersions': ['1'],
    'corsExposeHeaders': ['Etag'],
    'port': 80,
    'uri': 'http://127.0.0.1',
    'tornadoDebug': False
}

class AppPlugin(AppPluginBase):
    context = None
    urlHandlers = None
    tornadoApp = None
    httpServer = None

    def getId(self):
        return 'webServerPlugin'

    # pylint: disable=unused-argument
    def start(self, context):
        # Install asyncio/tornado bridge if not already initialized
        if not IOLoop.initialized():
            AsyncIOMainLoop().install()

        self.context = context

        # Get URL handlers for each API version
        self.urlHandlers = self.getApiSpecific('getUrlHandlers')

        # Define url handlers
        urls = {}
        for i, apiVersion in enumerate(self.urlHandlers):
            # If no API version is specified, we will use the oldest one
            if i == 0:
                urls.update(self.urlHandlers[apiVersion])

            versionUrls = self.urlHandlers[apiVersion]
            for url, handlerClass in versionUrls.items():
                urls['/v' + str(apiVersion) + url] = handlerClass
        urlHandlers = [mapping + (self.context,)
                for mapping in zip(urls.keys(), urls.values())]

        if urlHandlers:
            self.tornadoApp = tornado.web.Application(urlHandlers,
                    debug=self.context['tornadoDebug'], **context)

        self.context['tornadoApp'] = self.tornadoApp

        # Create a new HTTPServer
        self.httpServer = HTTPServer(self.tornadoApp, xheaders=True)

        # Start listening
        self.httpServer.listen(self.context['port'])

        IOLoop.current().add_callback(
                lambda: logger.info('Started web server'))

        self.callApiSpecific('start', self, self.context)


    def destroy(self, context):
        # Stop accepting new HTTP connections, then shutdown server after a
        # delay. This pattern is suggested by Ben Darnell (a maintainer of
        # Tornado):
        # https://groups.google.com/d/msg/python-tornado/NTJfzETaxeI/MaJ-hvTw4_4J
        self.httpServer.stop()

        self.callApiSpecific('destroy', self, self.context)


    def callApiSpecific(self, functionName, *args, **kwargs):
        for apiVersion in self.context.get('apiVersions', ['1']):
            versionMod = importlib.import_module(
                    self.context['appPackage'].__name__
                    + '.WebServer.v' + apiVersion)
            if hasattr(versionMod, functionName):
                getattr(versionMod, functionName)(*args, **kwargs)


    def getApiSpecific(self, functionName, *args, **kwargs):
        result = OrderedDict()
        for apiVersion in self.context.get('apiVersions', ['1']):
            versionMod = importlib.import_module(
                    self.context['appPackage'].__name__
                    + '.WebServer.v' + apiVersion)
            if hasattr(versionMod, functionName):
                result[apiVersion] = \
                        getattr(versionMod, functionName)(*args, **kwargs)
            else:
                result[apiVersion] = None

        return result
