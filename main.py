import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import socket
import threading
import json
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(json.dumps(data_dict).encode(), (HOST, PORT))

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def server_socket(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        while True:
            data, addr = sock.recvfrom(1024)
            data_dict = json.loads(data.decode())

            new_data = {str(datetime.now()): data_dict}

            file_path = pathlib.Path('storage/data.json')

            if file_path.exists():
                with open(file_path, 'r') as f:
                    saved_data = json.load(f)
            else:
                saved_data = {}

            saved_data.update(new_data)

            with open(file_path, 'w') as f:
                json.dump(saved_data, f, indent=4)


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        web_server = threading.Thread(target=http.serve_forever, args=())
        web_server.start()
    except KeyboardInterrupt:
        web_server = threading.Thread(target=http.server_close, args=())
        web_server.start()

    server = threading.Thread(target=server_socket, args=(HOST, PORT))

    server.start()

    print("Сервер HTTP працює на порту 3000, а сервер сокет UDP — на порту 5000.")
    try:
        server.join()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    run()


