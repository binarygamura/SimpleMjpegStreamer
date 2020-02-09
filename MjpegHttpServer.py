import threading, socket, logging, time, base64
from queue import Queue, Empty

# limit of images within the sendqueue for each client
# if reached, further images are dropped.
MAX_IMAGES_IN_QUEUE = 30


class ClientProcess(threading.Thread):

    def __init__(self, socket, address, exit_callback=None, boundary: str = 'you_shall_not_pass'):
        threading.Thread.__init__(self)
        self.socket = socket
        self.boundary = boundary
        self.LOGGER = logging.getLogger(__name__ + str(address))
        self.send_queue = Queue(MAX_IMAGES_IN_QUEUE)
        self.exit_callback = exit_callback
        self.auth_callback = None

    def close(self):
        self.socket.close()

    def send_simple_response(self, fp, content: str, status_code: int = 200, status_message: str = 'OK',
                             content_type: str = 'text/plain'):
        # 'Content-Type: multipart/x-mixed-replace;boundary={}\r
        response_text = '\r\n'.join((
            'HTTP/1.1 {} {}',
            'Server: SimpleMjpegStreamer',
            'Connection: close',
            'Content-Type: {}',
            'Content-Length: {}\r\n\r\n')).format(status_code, status_message, content_type, len(content))
        fp.write(response_text)
        fp.write(content)
        fp.flush()

    def send_mjpeg_response_head(self, fp):
        response_head = '\r\n'.join((
            'HTTP/1.1 200 OK',
            'Server: SimpleMjpegStreamer',
            'Connection: close',
            'Pragma: no-cache',
            'Cache-Control: no-cache',
            'Content-Type: multipart/x-mixed-replace;boundary=--{}\r\n\r\n')).format(self.boundary)
        fp.write(response_head)
        fp.flush()

    def send_image(self, fp, image_data, image_type: str = 'jpeg'):
        image_head = '\r\n'.join((
            '--{}',
            'Content-Type: image/{}',
            'Content-Length: {}\r\n\r\n')).format(self.boundary, image_type, len(image_data))
        fp.write(image_head)
        fp.flush()
        self.socket.send(image_data)

    def offer_image(self, image_data):
        if not self.send_queue.full():
            self.send_queue.put(image_data)

    def run(self):
        # read request line and request headers
        try:
            with self.socket.makefile(mode='rw') as fp:

                is_authencated = True if self.auth_callback is None else False
                # read request line
                line = fp.readline()
                # print('readline "{}"'.format(line))
                request_line_elements = line.split()
                # only GET request are supported
                if request_line_elements[0] != 'GET':
                    return self.send_simple_response(fp, 'method {} not supported'.format(request_line_elements[0]),
                                                     405, 'Method Not Allowed')

                # /image.mjpg is the only valid location
                if request_line_elements[1].lower() != '/image.mjpg':
                    return self.send_simple_response(fp, 'unable to find resource on server.', 404, 'File Not Found')

                line = fp.readline()
                # read http headers. we dont need them, we could skip them
                while line != '' and line is not None:
                    line = line.strip()
                    if line == '':
                        break
                    print('processing line {}'.format(line))
                    (header_key, header_value) = line.split(':', 1)
                    if is_authencated == False and header_key.lower() == 'authorization':
                        header_value = header_value.trim()
                        if header_value.startswith('Basic '):
                            decoded = base64.b64decode(header_value[6:])
                            (username, password) = decoded.split(':')
                            if self.auth_callback(username, password) == True:
                                is_authencated = True
                    line = fp.readline()

                if is_authencated == False:
                    return self.send_simple_response(fp, 'unauthorized access detected', 401, 'Unauthorized')
                # at this point we can start listening for images and pipe them to the client.
                self.send_mjpeg_response_head(fp)
                while True:
                    image_data = self.send_queue.get(30)
                    self.send_image(fp, image_data, 'jpeg')
        except BrokenPipeError:
            self.LOGGER.exception('client closed connection!')
        except Empty:
            self.LOGGER.exception('no images to send!')
        except Exception as e:
            self.LOGGER.exception('error while handling client process')
        finally:
            self.LOGGER.info('client process ended')
            # always close the socket!
            self.socket.close()
            # call the exit callback if there is one
            if self.exit_callback is not None:
                self.exit_callback(self)


class MjpegHttpServer(threading.Thread):
    """
        Simple implementation of a very limited http server
        capable of manging multiple cliens in parallel
        and broadcasting imagedata as an mjpeg stream
        to them. This server is heavily multithreaded and
        just an example and/or proove of concept.
    """

    def __init__(self, socket_port: int = 8088, bind_address: str = '0.0.0.0'):
        threading.Thread.__init__(self)
        self.socket_port = socket_port
        self.run_flag = True
        self.LOGGER = logging.getLogger(__name__)
        self.clients_lock = threading.Lock()
        self.clients = []

    def close(self):
        self.run_flag = False
        if self.server_socket is not None:
            self.server_socket.close()

    def broadcast_image(self, image_data):
        # get exclusive lock
        with self.clients_lock:
            # offer image to every currently connected client.
            for client in self.clients:
                client.offer_image(image_data)

    def start_polling_images(self, image_source):
        for image in image_source.get_images():
            self.broadcast_image(image)

    def create_exitcallback(self):
        def callback(client_process):
            with self.clients_lock:
                self.clients.remove(client_process)

        return callback

    def run(self):
        self.run_flag = True
        # create new server socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            self.server_socket = server_socket
            try:
                # bind it to a local address and port
                server_socket.bind(('0.0.0.0', self.socket_port))
                server_socket.listen(2)  # limit the number of sockets within the accept queue

                # run forest... run...
                while self.run_flag:
                    self.LOGGER.info('waiting for new connection')
                    # wait for new incoming connections.
                    (connection, client_address) = server_socket.accept()
                    # create a ClientProcess which is a Thread
                    client_process = ClientProcess(connection, client_address, self.create_exitcallback())
                    # start the client process to avoid blocking.
                    client_process.start()
                    # add the newly created client to the list of all clients.
                    with self.clients_lock:
                        self.clients.append(client_process)
                    self.LOGGER.info('started new client process')
            except Exception as e:
                self.LOGGER.exception('error while serving http requests.')
                pass
            finally:
                self.LOGGER.info('closing server socket')
                # always close the socket.
                server_socket.close()

