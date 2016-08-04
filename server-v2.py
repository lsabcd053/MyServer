import BaseHTTPServer
import os

class ServerException(Exception):
    def __init__(self,msg):
        Exception.__init__(self,msg)
        self.msg = msg

class case_no_file(object):
    def test(self,handler):
        return not os.path.exists(handler.full_path)

    def act(self,handler):
        raise ServerException("'{0}' not found".format(handler.full_path))

class case_existing_file(object):
    def test(self,handler):
        return os.path.isfile(handler.full_path)

    def act(self,handler):
        handler.handle_file(handler.full_path)

class case_always_fail(object):
    def test(self,handler):
        return True

    def act(self,handler):
        return ServerException("Unknow Object '{0}'".format(handler.full_path))

class case_directory_index_file(object):
    def index_path(self,handler):
        return os.path.join(handler.full_path,'index.html')

    def test(self,handler):
        return os.path.isdir(handler.full_path) and \
               os.path.isfile(self.index_path(handler))
    def act(self,handler):
        handler.handle_file(self.index_path(handler))

class case_directory_no_index_file(object):
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               not os.path.isfile(self.index_path(handler))
    def act(self,handler):
        handler.list_dir(handler.full_path)

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    Error_Page = """\
        <html>
        <body>
        <h1>Error accessing {path}</h1>
        <p>{msg}</p>
        </body>
        </html>
        """
    Listing_Page = '''\
        <html>
        <body>
        <ul>
        {0}
        </ul>
        </body>
        </html>
        '''
    Cases = [
        case_no_file,
        case_existing_file,
        case_directory_index_file,
        case_directory_no_index_file,
        case_always_fail
    ]

    def create_page(self):
        value = {
            'date_time':self.date_time_string(),
            'client_host':self.client_address[0],
            'client_port':self.client_address[1],
            'command':self.command,
            'path':self.path
        }
        page = self.Page.format(**value)
        return page

    def send_page(self,page):
        self.send_response(200)
        self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_GET(self):
        try:
            self.full_path = os.getcwd() + self.path

            for case in self.Cases:
                handler = case()
                if handler.test(self):
                    handler.act(self)
                    break
        except Exception as msg:
            self.handle_error(msg)

    def handle_file(self,full_path):
        try:
            with open(full_path,'rb') as reader:
                content = reader.read()
            self.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(self.path,msg)
            self.handle_error()

    def send_content(self,content,status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def list_dir(self,full_path):
        try:
            entries = os.listdir(full_path)
            bullets = ["<li><a href='{0}/{1}'>{1}</a></li>".format(self.path,e)
                       for e in entries if not e.startswith('.')]
            page = self.Listing_Page.format('\n'.join(bullets))
            self.send_content(page)
        except OSError as msg:
            msg = "'{0}' cannot be listed: {1}".format(self.path,msg)
            self.handle_error(msg)

    def handle_error(self,msg):
        contnt = self.Error_Page.format(path=self.path,msg = msg)
        self.send_content(contnt)

if __name__ == "__main__":
    serverAddress = ('',8899)
    server = BaseHTTPServer.HTTPServer(serverAddress,RequestHandler)
    server.serve_forever()
