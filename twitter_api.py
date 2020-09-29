from typing import Any, Dict, List

from requests_oauthlib import OAuth1Session

from config import API, API_SCR, T_TOKEN, T_TOKEN_SCR

VERSION = '1.1'
HEADER = f'https://api.twitter.com/{VERSION}/'


class Twitter:
    """Twitter API for python

    Args:
        header (str): Twitter API's URL header
        consumer_api_key (str): Consumer API Key
        consumer_api_secret_key (str): Consumer API Secret Key
        access_token (str): Access Token
        access_token_secret (str): Access Token Secret

    Attributes:
        header (str): Twitter API's URL header
        session (OAuth1Session): OAuth1 Session
    """

    def __init__(
            self,
            header=HEADER,
            consumer_api_key=API,
            consumer_api_secret_key=API_SCR,
            access_token=T_TOKEN,
            access_token_secret=T_TOKEN_SCR):
        self.header = header
        self.session = OAuth1Session(
            consumer_api_key,
            consumer_api_secret_key,
            access_token,
            access_token_secret)

    def post_tweet(self, text: str):
        """Updates the authenticating user's current status, also known as Tweeting.

        Args:
            text (str): The text of the status update.

        Raises:
            AssertionError: Error

        """
        url = self.header + 'statuses/update.json'
        payload = {'status': text}
        response = self.session.post(url, params=payload)
        data = response.json()
        assert 'errors' not in data, str(data['errors'])

    def get_my_tl(self, count=10) -> List[Dict[str, Any]]:
        """Specifies the number of records to retrieve.

        Args:
            count (int): Specifies the number of records to retrieve.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            AssertionError: Error

        """
        url = self.header + 'statuses/home_timeline.json'
        payload = {'count': count}
        response = self.session.get(url, params=payload)
        data = response.json()
        assert 'errors' not in data, str(data['errors'])
        return data

    def get_followers_ids(self, user_id=None, screen_name=None):
        """Returns user IDs for every user following the specified user.

        Args:
            user_id (str): The ID of the user for whom to return results.
            screen_name (str): The user name for whom to return results.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            AssertionError: Error

        """
        url = self.header + 'followers/ids.json'
        if user_id is not None:
            payload = {'user_id': user_id}
        elif screen_name is not None:
            payload = {'screen_name': screen_name}
        else:
            payload = {}
        response = self.session.get(url, params=payload)
        data = response.json()
        assert 'errors' not in data, str(data['errors'])
        return data

    def get_friends_ids(self, user_id=None, screen_name=None):
        """Returns user IDs for every user the specified user is following.

        Args:
            user_id (str): The ID of the user for whom to return results.
            screen_name (str): The user name for whom to return results.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            AssertionError: Error

        """
        url = self.header + 'friends/ids.json'
        if user_id is not None:
            payload = {'user_id': user_id}
        elif screen_name is not None:
            payload = {'screen_name': screen_name}
        else:
            payload = {}
        response = self.session.get(url, params=payload)
        data = response.json()
        assert 'errors' not in data, str(data['errors'])
        return data

    def show(self, user_id=None, screen_name=None):
        """Returns a variety of information about the specified user.

        Args:
            user_id (str): The ID of the user for whom to return results.
            screen_name (str): The user name for whom to return results.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            AssertionError: Error

        """
        url = self.header + 'users/show.json'
        if user_id is not None:
            payload = {'user_id': user_id}
        elif screen_name is not None:
            payload = {'screen_name': screen_name}
        else:
            raise ValueError
        response = self.session.get(url, params=payload)
        data = response.json()
        assert 'errors' not in data, str(data['errors'])
        return data
