import os
from curio import socket, ssl, Kernel

def create_listening_ssl_socket(address, certfile, keyfile):
    if os.path.isfile(certfile) and os.path.isfile(keyfile):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.options |= (
            ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_COMPRESSION
        )
        ssl_context.set_ciphers("ECDHE+AESGCM")
        ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        ssl_context.set_alpn_protocols(["h2"])

        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        csock = ssl_context.wrap_socket(sock)
        while True:
            try:
                csock.send(None)
            except StopIteration as e:
                sock = e.value
                sock.bind(address)
                sock.listen()
                return sock
    else:
        raise FileNotFoundError(certfile + " and/or " + keyfile + " 找不到证书文件, HTTP2为了安全, 必须使用加密证书.")
