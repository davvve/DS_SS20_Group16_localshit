import uuid
import time
from localshit.utils import utils
from localshit.utils.utils import logging
from localshit.utils.config import config


class Heartbeat:
    def __init__(self, hosts, election, socket_sender):
        self.hosts = hosts
        self.election = election
        self.socket_sender = socket_sender

        self.heartbeat_message = None
        self.own_address = utils.get_host_address()
        self.last_heartbeat_received = time.time()
        self.last_heartbeat_sent = (
            time.time() - config["heartbeat_intervall"]
        )  # substract 3 sec. so that first heartbeat is sent immediately
        self.wait_for_heartbeat = False

    def watch_heartbeat(self):
        # check, when was the last heartbeat from the left neighbour?
        time_diff = time.time() - self.last_heartbeat_received
        if time_diff >= config["heartbeat_timeout"]:
            failed_neighbour = self.hosts.get_neighbour(direction="right")

            # if own address, then do nothing
            if failed_neighbour is not self.own_address:
                # remove failed neighbour
                logging.info("Heartbeat: nothing received from %s" % failed_neighbour)
                self.hosts.remove_host(failed_neighbour)

                # send failure message as multicast
                new_message = "FF:%s:%s" % (failed_neighbour, self.own_address)
                self.socket_sender.send_message(new_message, type="multicast")

                # if this was leader, then start service announcement and leader election
                if failed_neighbour == self.election.elected_leader:
                    data = "%s:%s" % ("SA", self.own_address)
                    self.socket_sender.send_message(data, type="multicast")
                    time.sleep(1)
                    self.election.start_election(await_response=True)

            self.last_heartbeat_received = time.time()

    def send_heartbeat(self):
        # create heartbeat message and send it every 3 sec.
        time_diff = time.time() - self.last_heartbeat_sent
        if time_diff >= config["heartbeat_intervall"]:
            self.heartbeat_message = {
                "id": str(uuid.uuid4()),
                "sender": self.own_address,
                "timestamp": time.time(),
            }

            new_message = "HB:%s:%s" % (
                self.heartbeat_message["id"],
                self.heartbeat_message["sender"],
            )

            self.socket_sender.send_message(
                new_message, self.hosts.get_neighbour(), type="unicast"
            )

            logging.info("Heartbeat: send to %s" % self.hosts.get_neighbour())
            self.last_heartbeat_sent = time.time()

    def handle_heartbeat_message(self, addr, parts):
        # forward heartbeat message as it is, if not leader
        if self.election.isLeader is False:
            # check, if the heartbeat comes from the neighbour
            left_neighbour = self.hosts.get_neighbour(direction="left")
            right_neighbour = self.hosts.get_neighbour(direction="right")
            # cehck, if heartbeat comes from the right neighbour
            if addr[0] == right_neighbour:
                # forward message
                logging.info("Heartbeat: received. forward to %s" % left_neighbour)
                new_message = "HB:%s:%s" % (parts[1], parts[2])
                self.socket_sender.send_message(
                    new_message, left_neighbour, type="unicast"
                )

                # note time of last heartbeat
                self.last_heartbeat_received = time.time()
            else:
                logging.error("Heartbeat: received from wrong neighbour")
        else:
            # if leader, have a look at the message if it is from himself
            if self.heartbeat_message:
                if parts[1] == self.heartbeat_message["id"]:
                    logging.info("Heartbeat: received own heartbeat from %s." % addr[0])
                    self.heartbeat_message = None
                    self.last_heartbeat_received = time.time()

    def handle_failure_message(self, addr, parts):
        lost_host = parts[1]
        # remove failed host from list
        if lost_host != self.own_address:
            self.hosts.remove_host(lost_host)
