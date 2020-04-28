from datetime import datetime
import requests

from bs4 import BeautifulSoup

from twitter_api import Twitter

URLs = [
    'https://www.amazon.co.jp/Nintendo-Switch-ニンテンドースイッチ-ネオンブルー-バッテリー持続時間が長くなったモデル/dp/B07WXL5YPW/ref=lp_4731379051_1_2?s=videogames&ie=UTF8&qid=1588021125&sr=1-2',
    'https://www.amazon.co.jp/Nintendo-Switch-ニンテンドースイッチ-Joy-バッテリー持続時間が長くなったモデル/dp/B07WS7BZYF/ref=sr_1_1?__mk_ja_JP=カタカナ&dchild=1&keywords=任天堂スイッチ+本体&qid=1588029202&s=videogames&sr=1-1'
]


def main():
    flag = True
    for URL in URLs:
        r = requests.get(URL)
        soup = BeautifulSoup(r.text, 'html.parser')
        our_price = soup.find(id='priceblock_ourprice')
        if our_price is None:
            continue
        Twitter().post_tweet(
            str(datetime.now()) + '\n' + our_price.get_text() + '\n' + URL)
        flag = False
    if flag:
        message = 'Nintendo Switch is out of stock at Amazon.'
        Twitter().post_tweet(
            str(datetime.now()) + '\n' + message)


if __name__ == '__main__':
    main()
