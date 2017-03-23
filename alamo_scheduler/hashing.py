import hashlib


def md5(key):
    return int(hashlib.md5(key).hexdigest(), 16)


class RendezVous(object):

    def __init__(self, nodes=None, hash=md5):
        if nodes is None:
            nodes = []
        self.nodes = nodes
        self._hash = hash

    def add(self, node):
        self.nodes.append(node)

    def remove(self, node):
        self.nodes.remove(node)

    def clear(self):
        self.nodes = []

    def select(self, key):
        high_score = -1
        winner = None
        for node in self.nodes:
            score = self._hash(("%s-%s" % (node, key)).encode('utf8'))
            if score > high_score:
                high_score, winner = score, node

            elif score == high_score:
                high_score, winner = score, max(str(node), str(winner))
        return winner
