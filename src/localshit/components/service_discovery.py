"""
Service Discovery

This class works as listener to all socket connections in one place.
It manages all incoming messages and handles it to the concerning objects.
"""

from select import select
from localshit.utils.stop import StoppableThread
from localshit.utils import utils
import time
import threading
from localshit.utils import config
from localshit.utils.utils import logging


class ServiceDiscovery(StoppableThread):
    def __init__(
        self, service_announcement, hosts, election, heartbeat, isActive,
    ):
        super(ServiceDiscovery, self).__init__()
        self.service_announcement = service_announcement
        self.hosts = hosts
        self.election = election
        self.heartbeat = heartbeat
        self.isActive = isActive

        self.UCAST_PORT = config.config["ring_unicast_port"]
        self.MCAST_GRP = config.config["ring_multicast_address"]
        self.MCAST_PORT = config.config["ring_multicast_port"]

        self.socket_multicast = utils.get_multicast_socket()
        utils.bind_multicast(
            self.socket_multicast, MCAST_GRP=self.MCAST_GRP, MCAST_PORT=self.MCAST_PORT
        )

        self.socket_unicast = utils.get_unicast_socket()
        self.socket_unicast.bind(("0.0.0.0", self.UCAST_PORT))

    def work_func(self):
        """
        Manages all incoming messages on unicast and multicast socket
        """
        try:
            # listen to incoming messages on multicast and unicast
            inputready, outputready, exceptready = select(
                [self.socket_multicast, self.socket_unicast], [], [], 1,
            )

            for socket_data in inputready:
                # handle UDP socket connections
                data, addr = socket_data.recvfrom(1024)  # wait for a packet
                if data:
                    parts = data.decode().split(":")
                    if parts[0] == "SA":
                        self.service_announcement.handle_service_announcement(addr)
                    elif parts[0] == "SE":
                        self.election.forward_election_message(parts)
                    elif parts[0] == "HB":
                        # TODO: forward heartbeat
                        self.heartbeat.handle_heartbeat_message(addr, parts)
                    elif parts[0] == "FF":
                        self.heartbeat.handle_failure_message(addr, parts)
                    elif parts[0] == "RP":
                        logging.error("Reply from host: %s" % addr[0])
                        if addr[0] != utils.get_host_address():
                            self.hosts.add_host(addr[0])
                    else:
                        logging.error("Unknown message type: %s" % parts[0])

                    # reset heartbeat beacause of leader election or service announcement
                    self.heartbeat.last_heartbeat_received = time.time()
        except Exception as e:
            logging.error("Error: %s" % e)

        # check if announcement and election is over:
        if self.isActive is True:
            # send heartbeat messages
            if self.election.isLeader is True:
                self.heartbeat.send_heartbeat()

        # watch heartbeats
        th = threading.Thread(target=self.heartbeat.watch_heartbeat)
        th.start()
