from datetime import datetime, timedelta

from twitter_api import Twitter


def main():
    twitter = Twitter()
    tl = twitter.get_my_tl(count=10)
    pre_time = None
    time = datetime.now()
    str_time = str(time).split(".")[0]
    interval = timedelta(hours=1)
    for tweet in tl:
        text = tweet["text"].replace("Error. ", "")
        try:
            pre_time = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        break
    if pre_time is None or pre_time + interval < time:
        twitter.post_tweet("Error. " + str_time)


if __name__ == "__main__":
    main()
