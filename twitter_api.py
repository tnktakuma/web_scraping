from typing import Any, Dict, List

import requests
from requests_oauthlib import OAuth1Session

from config import (
    X_BEARER_TOKEN,
    X_CLIENT_ID,
    X_CLIENT_SECRET,
    X_CONSUMER_KEY,
    X_CONSUMER_SECRET,
)

VERSION = "2"
HEADER = f"https://api.twitter.com/{VERSION}/"


class TwitterAPIError(Exception):
    """Exception raised for Twitter API errors.

    Attributes:
        message (str): Explanation of the error
        errors (dict): The error details from the API response
    """

    def __init__(self, message: str, errors: Any = None):
        self.message = message
        self.errors = errors
        super().__init__(self.message)


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
        consumer_api_key=X_CONSUMER_KEY,
        consumer_api_secret_key=X_CONSUMER_SECRET,
        access_token=X_BEARER_TOKEN,
        access_token_secret=X_CLIENT_SECRET,
    ):
        self.header = header
        self.session = None
        # self.session = OAuth1Session(
        #     consumer_api_key,
        #     consumer_api_secret_key,
        #     access_token,
        #     access_token_secret,
        # )

    def post_tweet(self, text: str):
        """Updates the authenticating user's current status, a.k.a. Tweeting.

        Args:
            text (str): The text of the status update.

        Raises:
            TwitterAPIError: Error from Twitter API

        """
        url = self.header + "tweets"
        payload = {"text": text}
        # response = self.session.post(url, json=payload)
        response = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {X_BEARER_TOKEN}"},
        )
        data = response.json()
        print(data)
        if "errors" in data or "error" in data:
            raise TwitterAPIError(
                "Failed to post tweet",
                errors=data.get("errors", data.get("error")),
            )

    def get_my_tl(self, count=10) -> List[Dict[str, Any]]:
        """Specifies the number of records to retrieve.

        Args:
            count (int): Specifies the number of records to retrieve.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            TwitterAPIError: Error from Twitter API

        """
        url = self.header + "tweets/home_timeline"
        payload = {"max_results": min(count, 100)}
        response = self.session.get(url, params=payload)
        data = response.json()
        if "errors" in data or "error" in data:
            raise TwitterAPIError(
                "Failed to get timeline",
                errors=data.get("errors", data.get("error")),
            )
        return data

    def get_followers_ids(self, user_id=None, screen_name=None):
        """Returns user IDs for every user following the specified user.

        Args:
            user_id (str): The ID of the user for whom to return results.
            screen_name (str): The user name for whom to return results.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            TwitterAPIError: Error from Twitter API

        """
        # Note: Twitter API v2 requires user_id, screen_name is not supported
        if user_id is not None:
            url = self.header + f"users/{user_id}/followers"
        elif screen_name is not None:
            # First, get user_id from screen_name
            user_data = self.get_user_by_username(screen_name)
            user_id = user_data["data"]["id"]
            url = self.header + f"users/{user_id}/followers"
        else:
            raise ValueError("Either user_id or screen_name must be provided")

        response = self.session.get(url)
        data = response.json()
        if "errors" in data or "error" in data:
            raise TwitterAPIError(
                "Failed to get followers",
                errors=data.get("errors", data.get("error")),
            )
        return data

    def get_friends_ids(self, user_id=None, screen_name=None):
        """Returns user IDs for every user the specified user is following.

        Args:
            user_id (str): The ID of the user for whom to return results.
            screen_name (str): The user name for whom to return results.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            TwitterAPIError: Error from Twitter API

        """
        # Note: Twitter API v2 requires user_id, screen_name is not supported
        if user_id is not None:
            url = self.header + f"users/{user_id}/following"
        elif screen_name is not None:
            # First, get user_id from screen_name
            user_data = self.get_user_by_username(screen_name)
            user_id = user_data["data"]["id"]
            url = self.header + f"users/{user_id}/following"
        else:
            raise ValueError("Either user_id or screen_name must be provided")

        response = self.session.get(url)
        data = response.json()
        if "errors" in data or "error" in data:
            raise TwitterAPIError(
                "Failed to get following users",
                errors=data.get("errors", data.get("error")),
            )
        return data

    def show(self, user_id=None, screen_name=None):
        """Returns a variety of information about the specified user.

        Args:
            user_id (str): The ID of the user for whom to return results.
            screen_name (str): The user name for whom to return results.

        Returns:
            List[Dict[str, Any]]: The channel's messages

        Raises:
            TwitterAPIError: Error from Twitter API

        """
        if user_id is not None:
            url = self.header + f"users/{user_id}"
        elif screen_name is not None:
            return self.get_user_by_username(screen_name)
        else:
            raise ValueError("Either user_id or screen_name must be provided")

        response = self.session.get(url)
        data = response.json()
        if "errors" in data or "error" in data:
            raise TwitterAPIError(
                "Failed to get user information",
                errors=data.get("errors", data.get("error")),
            )
        return data

    def get_user_by_username(self, username: str):
        """Returns information about a user by username.

        Args:
            username (str): The username (without @) for whom to return
                results.

        Returns:
            Dict[str, Any]: The user information

        Raises:
            TwitterAPIError: Error from Twitter API

        """
        url = self.header + f"users/by/username/{username}"
        response = self.session.get(url)
        data = response.json()
        if "errors" in data or "error" in data:
            raise TwitterAPIError(
                "Failed to get user by username",
                errors=data.get("errors", data.get("error")),
            )
        return data


if __name__ == "__main__":
    twitter = Twitter()
    try:
        twitter.post_tweet("Hello, Twitter API v2!")
        print("Tweet posted successfully.")
    except TwitterAPIError as e:
        print(f"Error posting tweet: {e.message}, Details: {e.errors}")
