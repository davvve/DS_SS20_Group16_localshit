import logging
import struct
from enum import Enum
from localshit.utils.config import config
from socket import (
    socket,
    AF_INET,
    SOCK_DGRAM,
    SOCK_STREAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    IPPROTO_UDP,
    IP_MULTICAST_TTL,
    IP_MULTICAST_LOOP,
    IP_ADD_MEMBERSHIP,
    IPPROTO_IP,
    INADDR_ANY,
    inet_aton,
)


def get_logger():
    LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    level_name = config["loglevel"]
    level = LEVELS.get(level_name, logging.NOTSET)
    format = "%(asctime)s.%(msecs)03d %(threadName)-9s: %(message)s"
    logging.basicConfig(level=level, format=format, datefmt="%H:%M:%S")
    return logging.getLogger(__name__)


logging = get_logger()  # noqa! F811


def get_host_address(remote_server="google.com"):
    """
    Return the/a network-facing IP number for this system.
    """
    # hostname = gethostname()
    # return gethostbyname(hostname)

    with socket(AF_INET, SOCK_DGRAM) as s:
        s.connect((remote_server, 80))
        return s.getsockname()[0]


def get_multicast_socket():
    socket_mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    try:
        socket_mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    except AttributeError:
        pass
    socket_mcast.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 32)
    socket_mcast.setsockopt(IPPROTO_IP, IP_MULTICAST_LOOP, 1)

    return socket_mcast


def bind_multicast(socket_mcast, MCAST_GRP="224.1.1.1", MCAST_PORT=5007):
    socket_mcast.bind(("0.0.0.0", MCAST_PORT))
    mreq = struct.pack("4sl", inet_aton(MCAST_GRP), INADDR_ANY)
    socket_mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)


def get_unicast_socket():
    socket_ucast = socket(AF_INET, SOCK_DGRAM)
    socket_ucast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    return socket_ucast


def get_tcp_socket():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    return server_socket


def compare_adresses(first_address, second_address):
    """
    comapares which address is the higher identifier and returns True if first is higher, otherwise false
    """
    first = inet_aton(first_address)
    second = inet_aton(second_address)

    if first == second:
        logging.error("First address is same as second")
        return CompareResult.SAME
    elif first > second:
        return CompareResult.LARGER
    else:
        return CompareResult.LOWER


class CompareResult(Enum):
    LARGER = 1
    LOWER = 2
    SAME = 3
