"""
Main class for starting a frontend server.

"""
import traceback
import select
from localshit.utils import utils
from localshit.utils.config import config
from localshit.utils.utils import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
from os import curdir, sep
import json


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass


class FrontendServer:
    def __init__(self):
        WEBSERVER_PORT = config["frontend_webserver_port"]
        UNICAST_PORT = config["frontend_unicast_port"]
        self.own_address = utils.get_host_address()

        # Unicast Socket for backend server updates (leader election)
        self.socket_unicast = utils.get_unicast_socket()
        self.socket_unicast.bind(("", UNICAST_PORT))

        # Start Web Server
        self.Handler = self.MakeCustomHandler()
        self.server = ThreadingSimpleServer(("", WEBSERVER_PORT), self.Handler)

        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()

        logging.info("frontend started at %s:%s!" % (self.own_address, WEBSERVER_PORT))

        # Listen to backend servers for new elected leader.
        self.listen_for_leader_elections(self.socket_unicast)

    def listen_for_leader_elections(self, socket):
        while True:
            inputready, outputready, exceptready = select.select([socket], [], [], 1)

            for socket_data in inputready:
                data, addr = socket_data.recvfrom(1024)
                if data:
                    parts = data.decode().split(":")
                    if parts[0] == "LE":
                        logging.info("Leader elected: %s" % parts[1])
                        self.Handler.leader_id = parts[1]

    def MakeCustomHandler(self):
        """
        Helper Function to build custom Handler for web requests
        """

        class MyHandler(BaseHTTPRequestHandler):
            leader_id = "0.0.0.0"

            def __init__(self, *args, **kwargs):
                super(MyHandler, self).__init__(*args, **kwargs)

            def _set_headers(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

            def do_GET(self):
                try:
                    if self.path.endswith(
                        "leader"
                    ):  # path returns actual leader as json
                        json_resp = {"leader": self.leader_id}
                        json_str = json.dumps(json_resp)
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json_str.encode(encoding="utf_8"))
                    elif (
                        self.path.endswith(".png")
                        or self.path.endswith(".html")
                        or self.path.endswith(".ico")
                    ):  # returns html files, for example the index.php
                        f = open(curdir + sep + self.path, "rb")
                        self.send_response(200)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(f.read())
                        f.close()
                        return

                except IOError:
                    self.send_error(404, "File Not Found: %s" % self.path)

            def do_HEAD(self):
                self._set_headers()

        return MyHandler


def main():
    try:
        logging.info("starting frontend...")
        _ = FrontendServer()
    except Exception as e:
        logging.error("Error while starting app: %s" % e)
        traceback.print_exc()
