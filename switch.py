from datetime import datetime, timedelta
import requests
import re

from bs4 import BeautifulSoup

from twitter_api import Twitter

ITEM = [
    [
        "NINTENDO SWITCH gray",
        "https://www.amazon.co.jp/dp/B07WS7BZYF/ref=cm_sw_em_r_mt_dp_U_tTaTEbV33WCNW",
    ],
    [
        "NINTENDO SWITCH blue and red",
        "https://www.amazon.co.jp/dp/B07WXL5YPW/ref=cm_sw_em_r_mt_dp_U_PUaTEb9SBJ06M",
    ],
]


def main():
    twitter = Twitter()
    tl = twitter.get_my_tl(count=10)
    interval = timedelta(hours=1)
    for item in ITEM:
        name, url = item
        pre_time = None
        pre_price = None
        for tweet in tl:
            text = tweet["text"].split("\n")
            if len(text) == 4 and text[2] == name:
                try:
                    pre_time = datetime.strptime(text[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pre_time = None
                    continue
                pre_price = text[1]
                break
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        our_price = soup.find(id="priceblock_ourprice")
        time = datetime.now()
        str_time = str(time).split(".")[0]
        if our_price is None:
            template = str_time + "\nSOLD OUT\n" + name + "\n" + url
            if pre_time is None:
                twitter.post_tweet(template)
            elif pre_price != "SOLD OUT":
                twitter.post_tweet(template)
            elif pre_time + interval < time:
                twitter.post_tweet(template)
            continue
        price = our_price.get_text()
        int_price = int(re.sub(r"\D", "", price))
        template = str_time + "\n" + price + "\n" + name + "\n" + url
        if int_price > 35000:
            if pre_time is None:
                twitter.post_tweet(template)
            elif pre_price != price:
                twitter.post_tweet(template)
            elif pre_time + interval < time:
                twitter.post_tweet(template)
        elif int_price > 20000:
            twitter.post_tweet("@tnktakuma\n" + template)
        else:
            twitter.post_tweet("ERROR\n" + template)


if __name__ == "__main__":
    main()
