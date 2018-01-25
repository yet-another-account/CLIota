import shlex
import json
import logging
from cliota.api import node_mgr


def main():
    logging.basicConfig(level=logging.INFO)

    nodes = json.load(open('nodes.json'))
    node_mgr.ApiFactory(nodes)
