"""
Service Announcement

Adapted from https://stackoverflow.com/questions/21089268/python-service-discovery-advertise-a-service-across-a-local-network
"""

import time
from localshit.utils import utils
from localshit.utils.utils import logging


class ServiceAnnouncement:
    def __init__(self, hosts, socket_sender):
        self.hosts = hosts
        self.socket_sender = socket_sender

        self.own_address = utils.get_host_address()

    def announce_service(self, timeout=1):
        data = "%s:%s" % ("SA", self.own_address)
        self.socket_sender.send_message(data, type="multicast")
        logging.debug("SA: service announcement...")

        time.sleep(timeout)

        logging.info("SA: service announcement finished.")
        logging.info("Discovered hosts: %s" % self.hosts.sorted_ring)

    def handle_service_announcement(self, addr):
        if addr[0] != self.own_address:
            self.hosts.add_host(addr[0])
            self.hosts.form_ring(self.own_address)
            message = "RP:%s" % self.own_address
            self.socket_sender.send_message(message, addr[0], type="unicast")
