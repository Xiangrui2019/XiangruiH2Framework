class AbstractApp:
    def start(self):
        raise NotImplementedError
    
    def get(self, route: str, handler):
        raise NotImplementedError

    def post(self, route: str, handler):
        raise NotImplementedError

    async def handle_route(self, http, stream):
        raise NotImplementedError

class AbstractRouter:
    def register(self, method: str, route: str, handler):
        raise NotImplementedError

    async def handle_route(self, http, stream):
        raise NotImplementedError

class AbstractHTTP:
    async def handle_event(self, event):
        raise NotImplementedError

    async def send(self, stream_id, headers, data):
        raise NotImplementedError

class AbstractResponse:
    async def send(self, data: bytes):
        raise NotImplementedError

    async def send_file(self, file_path):
        raise NotImplementedError

    async def send_status_code(self, status_code):
        raise NotImplementedError

class AbstractRequest:
    def geturlparams(self, name):
	   	raise NotImplementedError