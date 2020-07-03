import time
import json
import random
import uuid
from localshit.utils.stop import StoppableThread
from localshit.utils.config import config
from localshit.utils.utils import logging
from localshit.components.websocket_server import WebsocketServer


class ContentProvider(StoppableThread):
    def __init__(self, election, reliable_socket, database):
        super(ContentProvider, self).__init__()
        self.election = election
        self.database = database
        self.server = WebsocketServer(config["content_websocket_port"], host="0.0.0.0")
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_client_left(self.client_left)
        self.server.set_fn_message_received(self.message_received)
        self.quote_id = uuid.uuid4()

        # need reliable_socket for data replication
        self.reliable_socket = reliable_socket
        self.reliable_socket.set_fn_delivered(self.multicast_delivered)

        logging.debug("Starting ContentProvider")

        self._ask_for_initial_database()

        self.last_update = time.time()

    def work_func(self):
        if self.election.isLeader:
            # only run content service if elected as leader
            if self.server.isRunning is False:
                # check if WebsocketServer is running
                try:
                    self.server.run_forever()
                    self.server.isRunning = True
                except Exception as e:
                    logging.error("Error while restarting server: %s" % e)
            else:
                if config["chuck_norris"] is True:
                    # optionally publish chuck norris quotes in a intervall
                    time_diff = time.time() - self.last_update
                    if time_diff >= config["quote_intervall"]:
                        logging.info("Content: publish new quote")
                        id, quote = self._get_quote("jokes.json")
                        data = "%s:%s:%s" % ("CO", id, quote)
                        self._replicate_and_send(data)

                        self.last_update = time.time()

        else:
            if self.server.isRunning is True:
                self.server.isRunning = False
                data = "%s:%s" % ("CL", "close server")
                self.server.send_message_to_all(data)
                self.server.shutdown()
                self.server.server_close()
                logging.info("Content: publish service stopped")

    def _get_quote(self, filename):
        quote = None
        quote_id = None

        try:
            file = open(filename)
            data = json.load(file)
            quotes = data["value"]
            counts = len(quotes)
            rand = random.randint(0, counts - 1)
            quote = quotes[rand]
            quote = quote["joke"]
            quote_id = uuid.uuid4()
        except Exception as e:
            logging.error("Content: Error while generating quote: %s" % e)

        return (quote_id, quote)

    def new_client(self, client, server):
        """Callback function of WebsocketServer on new client connected"""
        logging.info("Content: New client connected and was given id %d" % client["id"])

    def client_left(self, client, server):
        """Callback function of WebsocketServer on client left"""
        logging.info("Content: Client(%d) disconnected" % client["id"])

    def message_received(self, client, server, message):
        """Callback function of WebsocketServer on message received from client"""
        logging.info("Content: Message from client %d: %s" % (client["id"], message))

        parts = message.split(":")
        if parts[0] == "CR":
            new_message = "%s:%s:%s" % (parts[0], parts[1], parts[2])
            self.server.send_message_to_all(new_message)
        elif parts[0] == "CO":
            quote_id = uuid.uuid4()
            data = "%s:%s:%s" % ("CO", quote_id, parts[1])
            self._replicate_and_send(data)

    def multicast_delivered(self, sender, message):
        """Callback function of ReliableSocketWorker on new message delivered"""
        parts = message.split(":")
        if parts[0] == "AA" and self.election.isLeader:
            data_set = self.database.get_range(start=-20)
            for msg in data_set:
                self.reliable_socket.unicast_send(sender, msg)
        else:
            logging.debug('Delivered "%s" from %s' % (message[:15], sender))
            self.database.insert(message)

    def _replicate_and_send(self, data):
        # 1. replicate with other backend servers and itself to store quote to database
        try:
            self.reliable_socket.multicast(data)
        except Exception as e:
            logging.error("Content: Error while saving quote: %s" % e)
            return
        # 2. Send message to client
        try:
            self.server.send_message_to_all(data)
        except Exception as e:
            logging.error("Content: Error while sending quote: %s" % e)
            return

    def _ask_for_initial_database(self):
        data = "%s:%s" % ("AA", self.election.current_member_ip)
        try:
            self.reliable_socket.multicast(data)
        except Exception as e:
            logging.error("Content: Error while saving quote: %s" % e)
            return
