"""
Class for handle reliable multicast and unicast.

Inspired by https://github.com/daeyun/reliable-multicast-chat
"""
from queue import PriorityQueue
import socket
import struct
import threading
import time
import json
from localshit.utils import utils
from localshit.utils.utils import logging


class ReliableSocketWorker:
    def __init__(self, running, hosts, port=10033):
        self.port = port
        self.hosts = hosts
        self.running = running

        self.my_id = self.hosts.current_member_ip
        self.message_max_size = 4096
        self.message_id_counter = 0
        self.threads = []

        self.has_received = {}
        self.has_acknowledged = {}  # saves acknowledged messages
        self.unack_messages = []  # messages with pending acknowledgement
        self.holdback_queue = []

        self.holdback_sequence_counter = 0
        self.sequence_counter = 0
        self.SEQUENCER_ID = 0

        self.queue = PriorityQueue()
        self.mutex = threading.Lock()
        self.my_timestamp = {}
        for host in self.hosts.members:
            self.my_timestamp[host] = 0

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind((utils.get_host_address(), port))
        self.sock.settimeout(0.01)

    def unicast_send(
        self, destination, message, msg_id=None, is_ack=False, timestamp=None,
    ):
        """ Push an outgoing message to the message queue. """
        if timestamp is None:
            timestamp = self.my_timestamp

        is_msg_id_specified = msg_id is not None
        if msg_id is None:
            msg_id = self.message_id_counter

        # pack message with utils, make vector timestamp
        message = self.pack_message(
            [self.my_id, msg_id, is_ack, json.dumps(timestamp), message]
        )

        # append every new message excluding ack msg or without id to unack_messages. they will be removed as soon as message was acknowledged
        if not is_ack and not is_msg_id_specified:
            with self.mutex:
                self.unack_messages.append((destination, message))

        dest_ip = destination
        dest_port = self.port
        send_time = time.time()
        # put to queue, which sends the messages out
        self.queue.put((send_time, message, dest_ip, dest_port, msg_id))

    def unicast_receive(self):
        """ Receive UDP messages from other chat processes and store them in the holdback queue.
            Returns True if new message was received. """

        data, _ = self.sock.recvfrom(self.message_max_size)
        [sender, message_id, is_ack, message_timestamp, message] = self.unpack_message(
            data
        )

        logging.debug("Received #%s from %s" % (message_id, sender))

        # add sender to timestamps if not yet
        if sender not in self.my_timestamp:
            self.my_timestamp[sender] = message_timestamp[sender]

        # check if hosts in hold-back queue are up-to-date with ring
        new_timestamp = {}
        for host in self.my_timestamp:
            if host in self.hosts.members:
                new_timestamp[host] = self.my_timestamp[host]
        self.my_timestamp = new_timestamp

        # check if ack message type
        if is_ack:
            # save that ack was send
            self.has_acknowledged[(sender, message_id)] = True
        else:
            # if normal message, send acknowledgement to the sender
            self.unicast_send(sender, "ACK", msg_id=message_id, is_ack=True)
            # check if message was send more than once
            if (sender, message_id) not in self.has_received:
                self.has_received[(sender, message_id)] = True
                self.holdback_queue.append((sender, message_timestamp, message))
                self.update_holdback_queue_casual()
                return True
        return False

    def update_holdback_queue_casual(self):
        """ Compare message timestamps to ensure casual ordering. """
        while True:
            new_holdback_queue = []
            removed_messages = []
            logging.debug("Holdback-queue size: %s" % (len(self.holdback_queue)))
            # check with vector timestamp, if ordering is correct or some messages are missing
            for sender, v, message in self.holdback_queue:
                should_remove = True
                for item in v:
                    if item == sender:
                        if v[item] != self.my_timestamp[item]:
                            should_remove = False
                        if v[item] > self.my_timestamp[item]:
                            should_remove = False
                if not should_remove:
                    new_holdback_queue.append((sender, v, message))
                else:
                    removed_messages.append((sender, v, message))

            # deliver the messages which are removed from holdback queue in this update cycle
            for sender, v, message in removed_messages:
                self.my_timestamp[sender] += 1  # update own vector_clock timestamp
                self.deliver(sender, message)

            self.holdback_queue = new_holdback_queue

            if not removed_messages:
                break

    def multicast(self, message):
        """ Unicast the message to all known clients. """
        # immitate multicast as for loop with unicasts. only on this way we get reliable multicast
        for destination in self.hosts.members:
            self.unicast_send(destination, message)
        self.message_id_counter += 1

    def pack_message(self, message_list):
        return (";".join([str(x) for x in message_list])).encode("utf-8")

    def unpack_message(self, message):
        message = message.decode("utf-8")
        (sender, message_id, is_ack, vector_str, message,) = message.split(";", 4)

        message_id = int(message_id)
        timestamp = json.loads(vector_str)
        is_ack = is_ack in ["True", "true", "1"]

        return [sender, message_id, is_ack, timestamp, message]

    def ip2int(self, addr):
        return struct.unpack("!I", socket.inet_aton(addr))[0]

    def int2ip(self, addr):
        return socket.inet_ntoa(struct.pack("!I", addr))

    def message_queue_handler(self, running):
        """ Thread that actually sends out messages when send time <= current_time. """
        # TODO: if we have removed randomness in sending messages, can we simplify this?
        while running:
            (send_time, message, ip, port, msg_id) = self.queue.get(block=True)
            if send_time <= time.time():
                logging.debug("Send #%s to %s" % (msg_id, ip))
                self.sock.sendto(message, (ip, port))
            else:
                self.queue.put((send_time, message, ip, port, msg_id))
                time.sleep(0.01)

    def ack_handler(self, running):
        """ Thread that re-sends all unacknowledged messages. """
        while running:
            time.sleep(0.2)

            with self.mutex:
                new_unack_messages = []
                for dest_id, packed_message in self.unack_messages:
                    [
                        _,
                        message_id,
                        is_ack,
                        message_timestamp,
                        message,
                    ] = self.unpack_message(packed_message)
                    # check if message was not acknowledged and add it to new list, but send no ACK-ACK msg
                    if (dest_id, message_id) not in self.has_acknowledged:
                        new_unack_messages.append((dest_id, packed_message))
                self.unack_messages = new_unack_messages

    def incoming_message_handler(self, running):
        """ Thread that listens for incoming UDP messages """
        while running:
            try:
                self.unicast_receive()
            except (socket.timeout, BlockingIOError):
                pass

    def deliver(self, sender, message):
        """ Do something with the received message. """
        # TODO: save message to database
        if sender != self.hosts.current_member_ip:
            self.multicast_delivered(sender, message)
        else:
            logging.debug("received own message.")
            self.multicast_delivered(sender, message)

    def multicast_delivered(self, sender, message):
        pass

    def set_fn_delivered(self, fn):
        self.multicast_delivered = fn

    def run(self):
        """ Initialize and start all threads. """
        thread_routines = [
            self.ack_handler,
            self.message_queue_handler,
            self.incoming_message_handler,
        ]

        count = 1
        for thread_routine in thread_routines:
            thread = threading.Thread(
                target=thread_routine,
                args=(self.running,),
                name="ReliableSocketWorker-%s" % count,
            )
            thread.daemon = True
            thread.start()
            logging.info("Thread %s started." % thread.name)
            self.threads.append(thread)
            count += 1
