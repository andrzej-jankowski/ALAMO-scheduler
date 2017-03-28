import hashlib


class Hashing(object):

    def __init__(self, schedulers=None):
        self.nodes = schedulers or []

    def select(self, key):
        max_score = -1
        max_node = None
        for node in self.nodes:
            score = int(
                hashlib.md5(
                    ("%s-%s" % (node, key)).encode('utf8')
                ).hexdigest(), 16
            )

            if score > max_score:
                max_score, max_node = score, node
            elif score == max_score:
                max_score, max_node = score, max(str(node), str(max_score))

        return max_node
