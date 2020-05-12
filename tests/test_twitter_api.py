import unittest

from twitter_api import Twitter


class TestTwitter(unittest.TestCase):
    def setUp(self):
        self.twitter = Twitter()

    def test_get_my_tl(self):
        tl = self.twitter.get_my_tl(2)
        self.assertTrue(isinstance(tl, list))
        self.assertEqual(len(tl), 2)
        tweet = tl[0]
        self.assertTrue(isinstance(tweet, dict))
        for key in tweet:
            print(key)


if __name__ == '__main__':
    unittest.main()
