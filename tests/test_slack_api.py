import unittest

from config import MY_CID
from slack_api import Slack


class TestSlack(unittest.TestCase):
    def setUp(self):
        self.slack = Slack()

    def test_get_users(self):
        users = self.slack.get_users(2)
        self.assertTrue(isinstance(users, list))
        self.assertEqual(len(users), 2)
        user = users[0]
        self.assertTrue(isinstance(user, dict))

    def test_get_channels(self):
        channels = self.slack.get_channels(2)
        self.assertTrue(isinstance(channels, list))
        self.assertEqual(len(channels), 2)
        channel = channels[0]
        self.assertTrue(isinstance(channel, dict))

    def test_get_messages(self):
        messages = self.slack.get_messages(MY_CID, 2)
        self.assertTrue(isinstance(messages, list))
        self.assertEqual(len(messages), 2)
        message = messages[0]
        self.assertTrue(isinstance(message, dict))


if __name__ == '__main__':
    unittest.main()
