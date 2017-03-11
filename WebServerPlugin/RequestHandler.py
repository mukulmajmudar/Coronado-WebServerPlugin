import json
from functools import wraps
import asyncio

import tornado.web

from .Util import parseContentType

class RequestHandler(tornado.web.RequestHandler):
    context = None
    httpClient = None

    def initialize(self, **kwargs):
        # Initialize context with arguments
        self.context = kwargs

        # Set shortcut attributes on this object
        for key in self.context['shortcutAttrs']:
            setattr(self, key, self.context.get(key))


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


def withJsonBody(attrName='jsonBody', charset='UTF-8'):

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            contentType, reqCharset = parseContentType(
                    self.request.headers.get('Content-Type'))
            if contentType != 'application/json' or reqCharset != charset:
                raise tornado.web.HTTPError(415)
            try:
                setattr(self, attrName, json.loads(
                    self.request.body.decode(encoding='UTF-8')))
            except ValueError:
                raise tornado.web.HTTPError(415)
            else:
                result = func(self, *args, **kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                else:
                    return result

        return wrapper

    return decorator


def finish(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            func(*args, **kwargs)
        finally:
            if not self._finished:
                self.finish()

    return wrapper
