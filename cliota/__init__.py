import shlex
import json
import time
import logging
from cliota.api import node_mgr


def main():
    logging.basicConfig(level=logging.INFO)

    nodes = json.load(open('nodes.json'))
    apifactory = node_mgr.ApiFactory(nodes)

    # sleep forever
    # temporary bodge for until we get proper CLI implemented
    while True:
        time.sleep(999)
