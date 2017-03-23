from collections import defaultdict

from unittest import TestCase

from alamo_scheduler.hashing import RendezVous
from tests.base import UUIDS


class TestAlamoScheduler(TestCase):
    def setUp(self):
        self.hashing = RendezVous()
        self.checks_len = len(UUIDS)
        self.selection = defaultdict(list)

    def tearDown(self):
        self.hashing.clear()
        self.selection.clear()

    def test_add_remove(self):
        self.hashing.add('alamo-scheduler1')
        self.assertEqual(len(self.hashing.nodes), 1)

        self.hashing.remove('alamo-scheduler1')
        self.assertEqual(len(self.hashing.nodes), 0)

    def test_with_one_scheduler(self):
        scheduler = 'alamo-scheduler1'
        self.hashing.add(scheduler)
        for uuid in UUIDS:
            host = self.hashing.select(uuid)
            self.selection[host].append(uuid)

        self.assertEqual(len(self.selection[scheduler]), self.checks_len)

    def test_with_two_schedulers(self):
        schedulers = ['alamo-scheduler1', 'alamo-scheduler2']
        self.hashing.nodes = schedulers
        for uuid in UUIDS:
            host = self.hashing.select(uuid)
            self.selection[host].append(uuid)

        length = sum([len(v) for v in self.selection.values()])

        self.assertEqual(length, self.checks_len)
