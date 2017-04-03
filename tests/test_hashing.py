from collections import defaultdict

from unittest import TestCase

from alamo_scheduler.hashing import Hashing
from tests.base import UUIDS


class TestAlamoScheduler(TestCase):
    def setUp(self):
        self.hashing = Hashing()
        self.checks_len = len(UUIDS)
        self.selection = defaultdict(list)

    def tearDown(self):
        self.hashing.nodes.clear()
        self.selection.clear()

    def test_with_one_scheduler(self):
        self.hashing.nodes.append('alamo-scheduler1')
        for uuid in UUIDS:
            host = self.hashing.select(uuid)
            self.selection[host].append(uuid)

        self.assertEqual(
            len(self.selection['alamo-scheduler1']), self.checks_len
        )

    def test_with_two_schedulers(self):
        schedulers = ['alamo-scheduler1', 'alamo-scheduler2']
        self.hashing.nodes = schedulers
        for uuid in UUIDS:
            host = self.hashing.select(uuid)
            self.selection[host].append(uuid)

        length = sum([len(v) for v in self.selection.values()])

        self.assertEqual(length, self.checks_len)
