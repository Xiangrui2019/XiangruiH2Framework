import traceback
from curio import spawn
import h2.config
import h2.connection
import h2.events
from h2.exceptions import ProtocolError
from . import sslsocket, abstract, http
create_listening_ssl_socket = sslsocket.create_listening_ssl_socket
HTTP = http.HTTP

async def h2_server(address, certfile, keyfile, app: abstract.AbstractApp):
    sock = create_listening_ssl_socket(address, certfile, keyfile)
    print("服务器正在监听: %s:%d" % address)

    async with sock:
        while True:
            client, _ = await sock.accept()
            server = H2Server(client, app)
            await spawn(server.run())

class H2Server:
    def __init__(self, sock, app: abstract.AbstractApp):
        config = h2.config.H2Configuration(client_side=False, header_encoding='utf-8')
        self.sock = sock
        self.conn = h2.connection.H2Connection(config=config)
        self.http = HTTP(app=app, sock=self.sock, connection=self.conn)

    async def run(self):
        self.conn.initiate_connection()
        await self.sock.sendall(self.conn.data_to_send())
        while True:
            data = await self.sock.recv(65535)

            if not data:
                break
            try:
                events = self.conn.receive_data(data)
            except ProtocolError as e:
                traceback.print_exception(etype=e, value=e, tb=e.__traceback__)
                continue
            except Exception as e:
                traceback.print_exception(etype=e, value=e, tb=e.__traceback__)
                print("无法处理的异常, 程序即将退出!")
                exit()

            for event in events:
                await self.http.handle_event(event)
            await self.sock.sendall(self.conn.data_to_send())