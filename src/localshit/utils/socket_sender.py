from localshit.utils import utils
from localshit.utils.utils import logging


class SocketSender:
    def __init__(self):
        self.UCAST_PORT = 10001
        self.MCAST_GRP = "224.1.1.1"
        self.MCAST_PORT = 5007

        self.own_address = utils.get_host_address()

        self.socket_multicast = utils.get_multicast_socket()
        self.socket_unicast = utils.get_unicast_socket()

    def send_message(self, message, address=None, port=None, type="unicast"):

        if type == "unicast":
            self._send_unicast(message, address, port)
        elif type == "multicast":
            self._send_multicast(message, address, port)
        else:
            pass

    def _send_unicast(self, message, address, port):
        if port is None:
            port = self.UCAST_PORT

        if address is None:
            logging.error("No address given. Cannot send message.")
            return

        self.socket_unicast.sendto(message.encode(), (address, port))

    def _send_multicast(self, message, address, port):
        if port is None:
            port = self.MCAST_PORT

        if address is None:
            address = self.MCAST_GRP

        self.socket_multicast.sendto(message.encode(), (address, port))
