"""
Main class for starting a server instance.

"""
import time
import traceback
import threading
from localshit.components.ring import Ring
from localshit.components.election import Election
from localshit.components.service_discovery import ServiceDiscovery
from localshit.components.service_announcement import ServiceAnnouncement
from localshit.components.content_provider import ContentProvider
from localshit.components.heartbeat import Heartbeat
from localshit.components.database_provider import Database
from localshit.utils.socket_sender import SocketSender
from localshit.utils.reliable_socket_sender import ReliableSocketWorker
from localshit.utils import utils
from localshit.utils.utils import logging
from localshit.utils.config import config


class LocalsHitManager:
    def __init__(self, frontend=None):
        self.threads = []
        if frontend is None:
            self.frontend = config["frontend_server"]
        else:
            self.frontend = frontend
        self.running = True
        self.isActive = False
        logging.info("manager started!")

        # init socket connections
        self.socket_sender = SocketSender()

        self.own_address = utils.get_host_address()

        # init Ring
        self.hosts = Ring(self.own_address)
        # init service announcement object
        self.service_announcement = ServiceAnnouncement(self.hosts, self.socket_sender)
        # init election
        self.election = Election(self.socket_sender, self.hosts, frontend=frontend)
        # init database
        self.database = Database()

        # init ReliableSocketWorker
        self.reliable_socket = ReliableSocketWorker(
            self.running, self.hosts, port=config["reliable_socket"]
        )

        try:
            self.reliable_socket.run()
            self.heartbeat = Heartbeat(self.hosts, self.election, self.socket_sender)

            # initiate service discovery thread
            self.discovery_thread = ServiceDiscovery(
                self.service_announcement,
                self.hosts,
                self.election,
                self.heartbeat,
                self.isActive,
            )
            self.discovery_thread.start()
            self.threads.append(self.discovery_thread)

            # start service announcement after discovery
            self.service_announcement.announce_service(
                timeout=config["announcement_timeout"]
            )

            # start election after discovery
            self.election.start_election(await_response=True, timeout=1)

            self.discovery_thread.isActive = True

            # initiate Content Provider
            content_provider = ContentProvider(
                self.election, self.reliable_socket, self.database
            )
            content_provider.start()
            self.threads.append(content_provider)

            # monitor threads and exit on failing
            while self.running:
                for th in self.threads:
                    if not th.is_alive():
                        logging.info("Thread %s died." % th.__class__.__name__)
                        self.running = False
                        break

                time.sleep(0.2)

        except KeyboardInterrupt:
            logging.info("Process terminated by user")
        except Exception as e:
            logging.error("Error in run.py: %s" % e)
            traceback.print_exc()
        finally:
            # graceful shutdown
            self.isActive = False
            self.discovery_thread.isActive = False
            logging.info("stopping threads...")
            for th in self.threads:
                logging.info("Stopping thread %s." % th.__class__.__name__)
                th.stop()
            for th in self.threads:
                logging.info("Joining thread %s." % th.__class__.__name__)
                th.join()

            for thread in self.reliable_socket.threads:
                logging.info("Joining Thread %s." % thread.name)
                thread.join(0.2)

            main_thread = threading.currentThread()
            for t in threading.enumerate():
                if t is main_thread:
                    continue
                logging.info("Joining Thread %s." % thread.name)
                t.join(0.2)

            logging.info("threads stopped")
