"""CONNECT-only proxy. Run on an internal Docker network plus a separate egress network."""
import select
import socket
import socketserver

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        line=self.rfile.readline(8192).decode('ascii',errors='replace').strip().split()
        while self.rfile.readline(8192) not in (b'\r\n',b'\n',b''): pass
        if len(line)!=3 or line[:2]!=['CONNECT','api.anthropic.com:443']:
            self.wfile.write(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n');return
        with socket.create_connection(('api.anthropic.com',443),timeout=30) as upstream:
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n');self.wfile.flush()
            sockets=[self.connection,upstream]
            while True:
                ready,_,_=select.select(sockets,[],[],120)
                if not ready:return
                for source in ready:
                    data=source.recv(65536)
                    if not data:return
                    (upstream if source is self.connection else self.connection).sendall(data)

if __name__=='__main__':
    with socketserver.ThreadingTCPServer(('0.0.0.0',8080),Handler) as server:server.serve_forever()
