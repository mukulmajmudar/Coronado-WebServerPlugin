import importlib

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
            'port'
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


class AppPlugin(AppPluginBase):
    pluginId = 'webServerPlugin'
    context = None
    urlHandlers = None
    tornadoApp = None
    httpServer = None

    def setup(self, application, context):
        self.context = context
        self.urlHandlers = {}


    def addUrlHandlers(self, version, urlHandlers):
        if version in self.urlHandlers:
            self.urlHandlers[version].update(urlHandlers)
        else:
            self.urlHandlers[version] = urlHandlers


    def start(self, app, context):
        # Define url handlers
        urls = {}
        for i, apiVersion in enumerate(self.urlHandlers):
            # If no API version is specified, we will use the oldest one
            if i == 0:
                urls.update(self.urlHandlers[apiVersion])

            versionUrls = self.urlHandlers[apiVersion]
            for url, handlerClass in versionUrls.iteritems():
                urls['/v' + str(apiVersion) + url] = handlerClass
        logger.debug('URL mappings: %s', str(urls))
        urlHandlers = [mapping + (self.context,)
                for mapping in zip(urls.keys(), urls.values())]

        if urlHandlers:
            self.tornadoApp = tornado.web.Application(urlHandlers)

        self.context['tornadoApp'] = self.tornadoApp

        # Create a new HTTPServer
        self.httpServer = HTTPServer(self.tornadoApp, xheaders=self.xheaders)

        # Start listening
        self.httpServer.listen(self.context['port'])

        self.callApiSpecific('start', self, self.context)


    def stop(self):
        self.callApiSpecific('stop', self, self.context)

        # Stop accepting new HTTP connections, then shutdown server after a
        # delay. This pattern is suggested by Ben Darnell (a maintainer of
        # Tornado):
        # https://groups.google.com/d/msg/python-tornado/NTJfzETaxeI/MaJ-hvTw4_4J
        self.httpServer.stop()


    def destroy(self):
        self.callApiSpecific('destroy', self, self.context)


    def callApiSpecific(self, functionName, *args, **kwargs):
        for apiVersion in self.context.get('apiVersions', ['1']):
            versionMod = importlib.import_module(
                    self.context['appPackage'].__name__
                    + '.v' + apiVersion)
            if hasattr(versionMod, functionName):
                getattr(versionMod, functionName)(*args, **kwargs)
