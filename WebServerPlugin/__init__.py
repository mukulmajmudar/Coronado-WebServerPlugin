import importlib

import tornado.web
from tornado.httpserver import HTTPServer
from Coronado.Config import Config as ConfigBase
from Coronado.Plugin import AppPlugin as AppPluginBase

class Config(ConfigBase):

    def __init__(self, keys=None): 
        if keys is None:
            keys = []
        super(Config, self).__init__(
        [
            'allowedCORSOrigins',
            'apiVersions',
            'port',
            'uri'
        ] + keys)


    def _getAllowedCORSOrigins(self):
        '''
        List of origins allowed to access this server.
        '''
        return []


    def _getApiVersions(self):
        return ['1']


    def _getPort(self):
        return 80


    def _getUri(self):
        return 'http://127.0.0.1:{}'.format(self['port'])


class AppPlugin(AppPluginBase):
    pluginId = 'webServerPlugin'
    context = None
    urlHandlers = None
    tornadoApp = None
    httpServer = None

    # pylint: disable=unused-argument
    def start(self, app, context):
        self.context = context

        # Get URL handlers for each API version
        self.urlHandlers = self.getApiSpecific('getUrlHandlers')

        if not app._workerMode:
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
                self.tornadoApp = tornado.web.Application(urlHandlers)

            self.context['tornadoApp'] = self.tornadoApp

            # Create a new HTTPServer
            self.httpServer = HTTPServer(self.tornadoApp, xheaders=True)

            # Start listening
            self.httpServer.listen(self.context['port'])

        self.callApiSpecific('start', app, self, self.context)


    def destroy(self, app, context):
        if not app._workerMode:
            # Stop accepting new HTTP connections, then shutdown server after a
            # delay. This pattern is suggested by Ben Darnell (a maintainer of
            # Tornado):
            # https://groups.google.com/d/msg/python-tornado/NTJfzETaxeI/MaJ-hvTw4_4J
            self.httpServer.stop()

        self.callApiSpecific('destroy', app, self, self.context)


    def callApiSpecific(self, functionName, *args, **kwargs):
        for apiVersion in self.context.get('apiVersions', ['1']):
            versionMod = importlib.import_module(
                    self.context['appPackage'].__name__
                    + '.v' + apiVersion)
            if hasattr(versionMod, functionName):
                getattr(versionMod, functionName)(*args, **kwargs)


    def getApiSpecific(self, functionName, *args, **kwargs):
        result = {}
        for apiVersion in self.context.get('apiVersions', ['1']):
            versionMod = importlib.import_module(
                    self.context['appPackage'].__name__
                    + '.v' + apiVersion)
            if hasattr(versionMod, functionName):
                result[apiVersion] = \
                        getattr(versionMod, functionName)(*args, **kwargs)
            else:
                result[apiVersion] = None

        return result
