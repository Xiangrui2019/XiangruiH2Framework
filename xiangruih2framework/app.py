import os
from curio import Kernel
from . import abstract, server
from .http import HTTP, Stream
from .router import Router

AbstractApp = abstract.AbstractApp
h2_server = server.h2_server

def default_get(app):
	async def f(request, response):
		route = request.stream.headers[':path'].lstrip('/')
		full_path = os.path.join(app.root, route)
		if os.path.exists(full_path):
			await response.send_file(full_path)
		else:
			await response.send_status_code(404)
	return f

def get_index(app):
	async def f(request, response):
		await response.send_file(os.path.join(app.root, app.default_file))
	return f

class App(AbstractApp):
	def __init__(self, address="0.0.0.0", port=5000, root='./public',
				 auto_serve_static_file=True,
				 default_file='index.html', router=Router,
				 certfile='./localhost.crt.pem',
				 keyfile='./localhost.key'):
		self.port = port
		self.address = address
		self.root = os.path.abspath(root)
		self.default_file = default_file
		self.certfile = certfile
		self.keyfile = keyfile

		if auto_serve_static_file:
			self._router = router(default_get(self))
		else:
			self._router = router(None)
        
		if default_file:
			self.get('/', get_index(self))

	def start(self):
		kernel = Kernel()
		kernel.run(h2_server(address=(self.address, self.port),
							 certfile=self.certfile,
							 keyfile=self.keyfile,
							 app=self),
				   shutdown=True)

	def get(self, route: str, handler):
		self._router.register('GET', route, handler)

	def post(self, route: str, handler):
		self._router.register('POST', route, handler)

	async def handle_route(self, http: HTTP, stream: Stream):
		await self._router.handle_route(http, stream)