import datetime
import time
from typing import List, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.select import Select

from config import ARAKAWA_ID, ARAKAWA_PW

URL = "https://shisetsu.city.arakawa.tokyo.jp/stagia/reserve/gin_menu"


class ArakawaTennis:
    def __init__(self, headless=False, interval=10):
        options = Options()
        options.headless = headless
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(interval)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()
        del self.driver

    def start(self):
        # Open Arakawa Yoyaku URL
        self.driver.get(URL)
        self.driver.find_element(
            "xpath", '//input[@src="/stagia/jsp/images_jp/common/btn-complicated.gif"]'
        ).click()
        self.login()
        self.offer()

    def quit(self):
        self.driver.quit()

    def login(self):
        self.driver.find_element("id", "user").send_keys(ARAKAWA_ID)
        self.driver.find_element("id", "password").send_keys(ARAKAWA_PW)
        self.driver.find_element(
            "xpath", '//input[@src="/stagia/jsp/images_jp/multi_images/btn-login.gif"]'
        ).click()

    def offer(self):
        self.driver.find_element(
            "xpath", '//dl[@id="local-navigation"]/dd/ul/li[1]/a'
        ).click()
        # shurui
        select = Select(self.driver.find_element("id", "selectBunrui1"))
        select.select_by_value("1300")
        self.driver.find_element("id", "buttonSetBunrui1").click()
        # kubun
        select = Select(self.driver.find_element("id", "selectBunrui2"))
        select.select_by_value("1350")
        self.driver.find_element("id", "buttonSetBunrui2").click()
        # mokuteki
        select = Select(self.driver.find_element("id", "selectItem"))
        select.select_by_value("200")
        self.driver.find_element("id", "buttonSetItem").click()
        # shisetsu
        self.driver.find_element("id", "buttonAllSetShisetsu").click()
        self.driver.find_element("id", "buttonSetShisetsu").click()
        # basho
        select = Select(self.driver.find_element("id", "selectRoom"))
        for option in select.options:
            select.select_by_value(option.get_attribute("value"))
        self.driver.find_element("id", "buttonSetRoom").click()
        # search
        self.driver.find_element("id", "btnOK").click()

    def set_date(self, date: datetime.date):
        select = Select(self.driver.find_element("id", "YYYY"))
        select.select_by_value(str(date.year))
        select = Select(self.driver.find_element("id", "MM"))
        select.select_by_value(str(date.month))
        select = Select(self.driver.find_element("id", "DD"))
        select.select_by_value(str(date.day))
        self.driver.find_element("xpath", '//a[@href="javascript: search()"]').click()

    def parse_table(self, table):
        children = table.find_elements("xpath", "./*")
        data = []
        for child in children:
            if child.tag_name == "thead":
                ths = child.find_elements("tag name", "th")
                header = [th.text.replace("\n", "") for th in ths]
            elif child.tag_name == "tbody":
                th = child.find_elements("tag name", "th")[0]
                tds = child.find_elements("tag name", "td")
                for i, td in enumerate(tds):
                    if td.get_attribute("class") == "ok":
                        ok = td.find_elements("tag name", "input")
                        if ok and header[i]:
                            data.append(
                                [
                                    th.text.replace("\n", ""),
                                    header[i],
                                    ok[0].get_attribute("id"),
                                ]
                            )
        return data

    def get_avail(
        self, date_time: datetime.datetime = None
    ) -> List[Tuple[str, str, str]]:
        """Get whether any place is vacancy on the date.

        Args:
            date_time (datetime.datetime): the required date

        Retruns:
            List[Tuple[str, str, str]]: availability list.
        """
        self.start()
        self.set_date(date_time.date())
        table = self.driver.find_element("id", "1")
        avail_list = self.parse_table(table)
        return avail_list

    def reserve(self, date_time: datetime.datetime):
        """reserve tennis court

        Args:
            date_time (datetime.datetime): the required date
        """
        avail_list = self.get_avail(date_time)
        for avail in avail_list:
            if int(avail[1].split("～")[1].split(":")[0].strip()) < date_time.hour:
                ok_name, ok_time, ok_id = avail
                break
        else:
            return None
        self.driver.find_element("id", ok_id).click()
        self.driver.find_element("id", "btnYyList").click()
        select = Select(self.driver.find_element("id", "ryosyuhhSelect"))
        select.select_by_value("7")
        self.driver.find_element("xpath", '//a[@href="javascript: clickOK()"]').click()
        self.driver.find_element("xpath", '//a[@onclick="onConfirm()"]').click()
        # Alert(self.driver).accept()
        time.sleep(10)


def main():
    # Date
    today = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    tomorrow = today + datetime.timedelta(days=1)
    text = tomorrow.strftime("%Y年%m月%d日(%a)の空き情報") + "\n"
    with ArakawaTennis() as api:
        avail_list = api.get_avail(tomorrow)
        for avail in avail_list:
            print(" / ".join(avail))
    return avail_list


if __name__ == "__main__":
    main()
