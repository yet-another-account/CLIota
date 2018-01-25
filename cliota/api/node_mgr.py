import logging
import random
import iota
import timeout_decorator


logger = logging.getLogger(__name__)


class ApiFactory:
    def __init__(self, nodes):
        self.nodes = nodes
        self.apilocal = iota.Iota('http://0.0.0.0:0')
        self.apis = self.get_apis(num=4)

    def get_apis(self, num, exclude=[]):
        apis = []
        random.shuffle(self.nodes)

        for url in self.nodes:
            if url in exclude:
                continue

            try:
                api = iota.Iota(url)
                nodeinfo = self.__node_info(api, url)
                if not nodeinfo:
                    continue

                if nodeinfo['latestMilestoneIndex'] != nodeinfo['latestSolidSubtangleMilestoneIndex']:
                    logger.debug('Node %s is not synced!', url)
                    continue

                logger.info('Added node %s (LM: %d)!', url,
                            nodeinfo['latestMilestoneIndex'])

                # TODO: some efficient binary search insert thing
                apis.append((url, nodeinfo['latestMilestoneIndex']))

                apis.sort(key=lambda n: n[1], reverse=True)

                threshold = 2

                while len(apis) >= 2 and apis[-1][1] + threshold < apis[-2][1]:
                    logger.info('Dropped node %s from list (not up to sync)!',
                                apis[-1][0])
                    del apis[-1]

                if len(apis) >= num:
                    break

            except timeout_decorator.TimeoutError:
                logger.debug('Connection to node %s timed out!', url)

        return [a[0] for a in apis]

    @timeout_decorator.timeout(0.1, use_signals=False)
    def __node_info(self, api, url):
        try:
            return api.get_node_info()
        except Exception:
            logger.debug('Connection to node %s failed!', url)
            return None
