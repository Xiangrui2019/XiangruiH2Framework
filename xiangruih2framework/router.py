from .abstract import AbstractRouter
from .exceptions import RouteNotRegisteredException
from .http import HTTP, Stream, Request, Response


class Router(AbstractRouter):
	def __init__(self, default_get):
		self._routes = {
			'GET': {},
			'POST': {}
		}
		self.default_get = default_get

	def register(self, method: str, route: str, handler):
		assert method in ['GET', 'POST']
		self._routes[method][route] = handler

	def find_match(self, path: str):
		for routes_of_this_method in self._routes.values():
			for route in routes_of_this_method:
				matched, parameters = self._match(route, path)
				if matched:
					return route, parameters
		return None, None

	@classmethod
	def _match(cls, route, path):
		route = route.lstrip('/').rstrip('/').split('/')
		path = path.lstrip('/').rstrip('/').split('/')

		if len(route) != len(path):
			return False, None
		else:
			parameters = {}
			for r, p in zip(route, path):
				if r == p == '':
					return True, None
				if r == '' and r != p:
					return False, None
				if r[0] == '{' and r[-1] == '}':
					parameters[r[1:-1]] = p
				elif r != p:
					return False, None
			return True, parameters
    
	async def handle_route(self, http: HTTP, stream: Stream):
		path = stream.headers[':path']
		method = stream.headers[':method']

		route, parameters = self.find_match(path)
		if route is None:
			if method == 'GET':
				handler = self.default_get
			else:
				handler = None
		else:
			handler = self._routes[method].get(route, None)

		if handler is not None:
			req = Request(stream, parameters)
			res = Response(stream.stream_id, http)
			await handler(req, res)
		else:
			raise RouteNotRegisteredException(path + ' 没有注册对应的路由')