import socket
from localshit.utils.utils import logging


class Ring:
    members = []
    sorted_ring = []
    clients = []

    def __init__(self, current_member_ip):
        logging.debug("Ring initialized")
        self.current_member_ip = current_member_ip
        self.add_host(self.current_member_ip)

    def _form_ring(self, members):
        sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
        sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
        return sorted_ip_ring

    def add_host(self, host):
        if host not in self.members:
            self.members.append(host)
            self.sorted_ring = self._form_ring(self.members)
        else:
            logging.debug("Host %s was already discovered" % host)

    def remove_host(self, host):
        if host in self.members:
            self.members.remove(host)
            self.sorted_ring = self._form_ring(self.members)
        else:
            logging.debug("Host %s was already removed" % host)

    def add_client(self, host):
        if host not in self.clients:
            self.clients.append(host)
        else:
            logging.debug("Client %s was already added" % host)

    def get_hosts(self):
        return self.members

    def form_ring(self, own_ip):
        self.sorted_ring = self._form_ring(self.members)
        logging.info("Discovered hosts: %s" % self.sorted_ring)
        left_member = self.get_neighbour(direction="left")
        logging.info("Own IP: %s | left Neighbour: %s" % (own_ip, left_member))

        right_member = self.get_neighbour(direction="right")
        logging.info("Own IP: %s | right Neighbour: %s" % (own_ip, right_member))

    def get_neighbour(self, direction="left"):
        current_member_index = (
            self.sorted_ring.index(self.current_member_ip)
            if self.current_member_ip in self.sorted_ring
            else -1
        )
        if current_member_index != -1:
            if direction == "left":
                if current_member_index + 1 == len(self.sorted_ring):
                    return self.sorted_ring[0]
                else:
                    return self.sorted_ring[current_member_index + 1]
            else:
                if current_member_index - 1 == 0:
                    return self.sorted_ring[0]
                else:
                    return self.sorted_ring[current_member_index - 1]
        else:
            return None
