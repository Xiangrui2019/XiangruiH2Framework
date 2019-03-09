import mimetypes
from collections import OrderedDict
from curio import Event, aopen, spawn
from h2 import events
from h2.connection import H2Connection
from hyper2web.exceptions import DifferentStreamIdException
from .abstract import (AbstractApp, AbstractHTTP, AbstractRequest,
                       AbstractResponse)

READ_CHUNK_SIZE = 8096

class Stream:
	def __init__(self, stream_id: int, headers: dict):
		if headers and isinstance(headers, dict):
			self.stream_id = stream_id
			self.headers = headers
			self.buffered_data = []
			self.data = None
		else:
			raise Exception('http.Stream: 尝试构造一个没有有效headers的Stream')

	def update(self, event: events.DataReceived):
		if event.stream_id == self.stream_id:
			self.buffered_data.append(event.data)
		else:
			raise DifferentStreamIdException()

	def finalize(self):
		if len(self.buffered_data) > 0:
			self.data = b''.join(self.buffered_data)
		self.buffered_data = None

class HTTP(AbstractHTTP):
	def __init__(self, app: AbstractApp, sock, connection: H2Connection):
		self.streams = {}
		self.app = app
		self.sock = sock
		self.connection = connection
		self.flow_control_events = {}

	def _finalize_stream(self, stream_id):
		stream = self.streams.pop(stream_id)
		stream.finalize()
		return stream
    
	async def _check_event_end_stream(self, event):
		if event.stream_ended:
			stream = self._finalize_stream(event.stream_id)
			await self.app.handle_route(self, stream)

	async def handle_event(self, event: events.Event):
		if isinstance(event, events.RequestReceived):
			task = await spawn(self.request_received(event))
			await task.join()
		elif isinstance(event, events.DataReceived):
			await spawn(self.data_received(event))

		elif isinstance(event, events.WindowUpdated):
			await self.window_updated(event)

	async def request_received(self, event: events.RequestReceived):
		if event.stream_id in self.streams:
			raise Exception('RequestReceived 只存在与New的Stream中')
		else:
			self.streams[event.stream_id] = Stream(event.stream_id, dict(event.headers))
        
		await self._check_event_end_stream(event)

	async def data_received(self, event: events.DataReceived):
		if event.stream_id not in self.streams:
			raise Exception('headers前出现了数据')

		self.streams[event.stream_id].update(event)
		await self._check_event_end_stream(event)

	async def wait_for_flow_control(self, stream_id):
		evt = Event()
		self.flow_control_events[stream_id] = evt
		await evt.wait()

	async def window_updated(self, event):
		stream_id = event.stream_id

		if stream_id and stream_id in self.flow_control_events:
			evt = self.flow_control_events.pop(stream_id)
			await evt.set()
		elif not stream_id:
			blocked_streams = list(self.flow_control_events.keys())
			for stream_id in blocked_streams:
				event = self.flow_control_events.pop(stream_id)
				await event.set()

	async def send(self, stream_id: int, headers, data: bytes=None):

		if data is None:
			self.connection.send_headers(stream_id, headers, end_stream=True)
			await self.sock.sendall(self.connection.data_to_send())
		else:
			print('本次HTTP2请求的响应头:', headers)
			self.connection.send_headers(stream_id, headers, end_stream=False)
			await self.sock.sendall(self.connection.data_to_send())
			i = 0
			while True:
				while not self.connection.local_flow_control_window(stream_id):
					await self.wait_for_flow_control(stream_id)

				chunk_size = min(self.connection.local_flow_control_window(stream_id), READ_CHUNK_SIZE)

				data_to_send = data[i:i+chunk_size]
				end_stream = (len(data_to_send) != chunk_size)

				try:
					self.connection.send_data(stream_id, data_to_send, end_stream=end_stream)
				except BaseException as e:
					print("出现了错误:", e)

				await self.sock.sendall(self.connection.data_to_send())
				if end_stream:
					break
				i += chunk_size

class Request(AbstractRequest):
	def __init__(self, stream, para):
		self.stream = stream
		self.parameter = para
	
	def geturlparams(self, name):
	   	return self.parameter[name]

class Response(AbstractResponse):
	def __init__(self, stream_id: int, http: HTTP):
		self.stream_id = stream_id
		self.http = http
		self.headers = OrderedDict([
			(':status', '200'),
			('content-length', '0'),
			('server', 'XiangruiH2Framework')
		])

	def set_header(self, field, value):
		self.headers[field] = value

	def set_headers(self, headers):
		self.headers = headers

	def update_headers(self, headers):
		self.headers.update(headers)

	async def send_file(self, file_path):
		async with aopen(file_path, mode='rb') as f:
			data = await f.read()
			self.headers['content-length'] = str(len(data))
			content_type, content_encoding = mimetypes.guess_type(file_path)
			if content_type:
				self.headers['content-type'] = content_type
			if content_encoding:
				self.headers['content-encoding'] = content_encoding
			await self.send(data)

	async def send_status_code(self, status_code):
		self.headers[':status'] = str(status_code)
		await self.send(None)

	async def send(self, data: bytes or None):
		headers = tuple(self.headers.items())
		await self.http.send(self.stream_id, headers, data)