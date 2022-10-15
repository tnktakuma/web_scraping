import datetime

from kyoto_api import KyotoTennis
from twitter_api import Twitter


def get_text():
    # Date
    today = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    tomorrow = today + datetime.timedelta(days=1)
    text = tomorrow.strftime("%Y年%m月%d日(%a)の空き情報") + "\n"
    for i, place in enumerate(["西院公園", "岡崎公園", "宝が池公園"]):
        text += "\n" + place + "\n"
        with KyotoTennis() as api:
            avail_list = api.get_avail(i, tomorrow)
        for term, avail in avail_list:
            if avail:
                text += f"{term[0]}-{term[1]} "
            else:
                text += "x "
        text += "\n"
    return text


def main():
    Twitter().post_tweet(get_text())
    print("Tweeted")


if __name__ == "__main__":
    main()
