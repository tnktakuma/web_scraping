import requests
from typing import Any, Dict, List

from config import MY_UID, MY_CID, S_TOKEN

HEADER = "https://slack.com/api/"


class Slack:
    """Slack API for python

    Args:
        header (str): Slack API's URL header
        token (str): Slack API's Token

    Attributes:
        header (str): Slack API's URL header
        token (str): Slack API's Token

    """

    def __init__(self, header=HEADER, token=S_TOKEN):
        self.header = header
        self.token = token

    def post_message(self, channel: str, text: str):
        """Sends a message to a channel.

        Args:
            channel (str): Channel or private group to send message to.
            text (str): The content of the message

        Raises:
            AssertionError: 404 Error

        """
        url = self.header + "chat.postMessage"
        payload = {"token": self.token, "channel": channel, "text": text}
        response = requests.get(url, params=payload)
        data = response.json()
        assert data["ok"], "404 error"

    def get_messages(self, channel: str, limit=100) -> List[Dict[str, Any]]:
        """Fetches a conversation's history of messages and events.

        Args:
            channel (str): Conversation ID to fetch history for.
            limit (int): The maximum number of items to return.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            AssertionError: 404 Error

        """
        url = self.header + "conversations.history"
        payload = {"token": self.token, "channel": channel, "limit": limit}
        response = requests.get(url, params=payload)
        data = response.json()
        assert data["ok"], "404 error"
        return data["messages"]

    def get_users(self, limit=0) -> List[Dict[str, Any]]:
        """Lists all users in a Slack team.

        Args:
            limit (int): The maximum number of items to return.

        Returns:
            List[Dict[str, Any]]: A list of paginated user objects, in no particular order.

        Raises:
            AssertionError: 404 Error

        """
        url = self.header + "users.list"
        payload = {"token": self.token, "limit": limit}
        response = requests.get(url, params=payload)
        data = response.json()
        assert data["ok"], "404 error"
        return data["members"]

    def get_channels(self, limit=100) -> List[Dict[str, Any]]:
        """Lists all channels in a Slack team.

        Args:
            limit (int): The maximum number of items to return.

        Returns:
            List[Dict[str, Any]]: A list of limited channel-like conversation objects.

        Raises:
            AssertionError: 404 Error

        """
        url = self.header + "conversations.list"
        payload = {"token": self.token, "limit": limit}
        response = requests.get(url, params=payload)
        data = response.json()
        assert data["ok"], "404 error"
        return data["channels"]


if __name__ == "__main__":
    slack = Slack()
    slack.post_message(MY_CID, "Hello, World.")
