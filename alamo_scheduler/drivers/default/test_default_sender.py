from unittest import TestCase
from unittest.mock import patch, Mock

from alamo_scheduler.drivers.default.sender import DefaultSender


class TestDefaultSender(TestCase):

    @patch("alamo_scheduler.drivers.default.sender.ZeroMQQueue", Mock())
    def setUp(self):
        self.sender = DefaultSender()
        self.check = {
            'uuid': '997e8667-6e80-4131-a938-caa02d743550',
            'name': 'foo bar'
        }

    def test_send(self):
        send_mock = Mock()
        self.sender.queue = send_mock

        self.sender.send(self.check)
        self.assertTrue(send_mock.send.called)
