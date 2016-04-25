import tornado.websocket

# pylint: disable=abstract-method
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    context = None
    ioloop = None
    database = None
    httpClient = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        # Initialize context with arguments
        self.context = kwargs

        # Set shortcut attributes on this object
        for key in self.context['shortcutAttrs']:
            setattr(self, key, self.context.get(key))


    def check_origin(self, origin):
        allowedWSOrigins = self.context['allowedWSOrigins']
        return allowedWSOrigins == 'any' or origin in allowedWSOrigins


    def options(self, *args, **kwargs):
        pass


    def setCORSHeaders(self):
        # Manage cross-origin access
        allowedCORSOrigins = self.context['allowedCORSOrigins']
        if 'Origin' in self.request.headers \
                and (allowedCORSOrigins == 'any'
                        or self.request.headers['Origin'] in
                        self.context['allowedCORSOrigins']):
            self.set_header('Access-Control-Allow-Origin',
                    self.request.headers['Origin'])
            self.set_header('Access-Control-Allow-Methods',
                    'GET, POST, PUT, DELETE, OPTIONS')
            self.set_header('Access-Control-Allow-Credentials', 'true')
            if 'Access-Control-Request-Headers' in self.request.headers:
                self.set_header('Access-Control-Allow-Headers',
                    self.request.headers['Access-Control-Request-Headers'])

            corsExposeHeaders = self.context.get('corsExposeHeaders') 
            if corsExposeHeaders:
                self.set_header('Access-Control-Expose-Headers',
                        ','.join(corsExposeHeaders))


    def prepare(self):
        super().prepare()
        self.setCORSHeaders()


    def write_error(self, status, **kwargs):    # pylint: disable=unused-argument
        self.setCORSHeaders()


    def data_received(self, chunk):
        pass
