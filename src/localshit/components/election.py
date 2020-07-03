import time
from localshit.utils import utils
from localshit.utils import config
from localshit.utils.utils import logging
from localshit.utils.utils import CompareResult


class Election:
    def __init__(self, socket_sender, hosts, frontend):
        # first, mark member as non-participant
        self.participant = False
        self.socket_sender = socket_sender
        self.hosts = hosts
        self.current_member_ip = self.hosts.current_member_ip
        self.frontend_address = frontend
        self.isLeader = False
        self.got_response = False
        self.elected_leader = ""
        self.CONTENT_PORT = config.config["frontend_unicast_port"]

        logging.info("Election Class initialized")

    def start_election(self, await_response=False, timeout=1):
        logging.info("starting election")
        # mark self as a participant
        self.participant = True

        # send message to left neighbour
        message = "SE:%s:%s" % (self.current_member_ip, self.isLeader)
        neighbour = self.hosts.get_neighbour()

        self.socket_sender.send_message(message, neighbour, type="unicast")

        if await_response is True:
            self._wait_for_response(timeout)

    def _wait_for_response(self, timeout):

        # wait a leader is elected or timeout is over
        last_response = time.time()
        while self.elected_leader == "":
            if time.time() - last_response > timeout:
                logging.info("Leader Election: No response within timeout.")
                self.elected_leader = self.current_member_ip
                self.isLeader = True
                self.send_election_to_frontend()
                break
            time.sleep(0.1)

    def send_election_to_frontend(self):
        new_message = "LE:%s" % self.elected_leader
        self.socket_sender.send_message(
            new_message, self.frontend_address, port=self.CONTENT_PORT, type="unicast"
        )

    def forward_election_message(self, message):
        compare = utils.compare_adresses(message[1], self.current_member_ip)

        sender_id = message[1]
        leader_elected = eval(message[2])

        if leader_elected is False:
            if compare is CompareResult.LARGER:
                # 4.1 if id is larger, forward message to next member
                logging.info("Leader Election: Forward message as it is.")
                self.participant = True
                new_message = "SE:%s:%s" % (sender_id, False)
                self.socket_sender.send_message(
                    new_message, self.hosts.get_neighbour(), type="unicast"
                )
            elif compare is CompareResult.LOWER and self.participant is False:
                # 4.2 if id is smaller and not yes marked as participant, replace id and forward message to next member.
                self.participant = True
                logging.info("Leader Election: Forward message with own id.")
                new_message = "SE:%s:%s" % (self.current_member_ip, False)
                self.socket_sender.send_message(
                    new_message, self.hosts.get_neighbour(), type="unicast"
                )
            elif compare is CompareResult.LOWER and self.participant is True:
                # 4.3 if id is smaller but already participant, then discard message
                logging.info(
                    "Leader Election: Already participant of an election. Discard message."
                )
            elif compare is CompareResult.SAME:
                # 4.4 if message came back, set itself as leader and start second part algorithm. Inform others about elected leader.
                logging.info(
                    "Leader Election: Message came back to sender. Elected as leader."
                )
                self.participant = False
                self.isLeader = True
                self.elected_leader = self.current_member_ip
                # start second part of algorithm, inform others about election
                new_message = "SE:%s:%s" % (self.current_member_ip, True)
                self.socket_sender.send_message(
                    new_message, self.hosts.get_neighbour(), type="unicast"
                )
                self.send_election_to_frontend()
            else:
                logging.error("Leader Election: invalid result")
        else:
            # forward message about elected leader
            if sender_id is self.current_member_ip:
                logging.info(
                    "Leader Election: Message came back to sender. Election is over. Elected Leader: %s"
                    % self.elected_leader
                )
                self.send_election_to_frontend()
            elif self.participant is True:
                # elected message received. mark as non-participant, record election and forward message
                self.participant = False
                self.isLeader = False
                self.elected_leader = sender_id
                logging.info(
                    "Leader Election: Forward election message. Elected Leader: %s"
                    % self.elected_leader
                )
                new_message = "SE:%s:%s" % (message[1], message[2])
                self.socket_sender.send_message(
                    new_message, self.hosts.get_neighbour(), type="unicast"
                )
            else:
                logging.info(
                    "Leader Election: Election is over. Elected Leader: %s"
                    % self.elected_leader
                )
                self.send_election_to_frontend()
                
