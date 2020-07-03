import traceback
import argparse
from localshit.run import LocalsHitManager
from localshit.utils.utils import logging

import os


def main():
    frontend = "192.168.0.179"
    parser = argparse.ArgumentParser(prog="my_megazord_program")
    parser.add_argument(
        "-f", "--frontend", help='start with localshit -f "172.17.0.2" to add frontend'
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="start localhost and wait for VS Code debugger",
        action="store_true",
    )
    args = parser.parse_args()
    if args.frontend:
        frontend = args.frontend

    if args.debug:
        import debugpy

        debugpy.listen(5678)
        print("Waiting for debugger attach: %s" % os.getpid())
        debugpy.wait_for_client()

    logging.info("Frontend server is set to %s" % frontend)

    try:
        logging.info("starting manager...")
        _ = LocalsHitManager(frontend=frontend)
    except Exception as e:
        logging.error("Error while starting app: %s" % e)
        traceback.print_exc()
