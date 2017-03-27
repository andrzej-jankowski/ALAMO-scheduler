from unittest import TestCase
from unittest.mock import patch, Mock

from alamo_scheduler.zero_mq import ZeroMQ


class ZeroMQTestCase(TestCase):
    def setUp(self):
        self.environments = ['prod', 'test', 'dev']
        self.host = 'tcp://127.0.0.1'
        self.port = 5559

    @patch('alamo_scheduler.zero_mq.ZeroMQQueue.connect')
    def test_initialize(self, connect_mock):
        zmq = Mock()
        connect_mock.return_value = zmq
        zero = ZeroMQ(self.environments, self.host, self.port)
        for i, env in enumerate(self.environments, start=self.port):
            self.assertIsNotNone(getattr(zero, env, None))
            self.assertEqual(getattr(zero, env).host, self.host)
            self.assertEqual(getattr(zero, env).port, i)

        self.assertTrue(connect_mock.called)
