from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select

from config import TIMES_NO1, TIMES_NO2, TIMES_PWD

URL = "https://share.timescar.jp/about/option/studless/"


class TimesCarShareSnow:
    def __init__(self, headless=True, interval=5):
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
        # Open URL
        self.driver.get(URL)
        self.login()
        self.driver.get(URL)

    def quit(self):
        self.driver.quit()

    def login(self):
        self.driver.find_element(
            "xpath",
            '//a[@href="/view/member/mypage.jsp"]'
        ).click()
        self.driver.find_element("id", "cardNo1").send_keys(TIMES_NO1)
        self.driver.find_element("id", "cardNo2").send_keys(TIMES_NO2)
        self.driver.find_element("id", "tpPassword").send_keys(TIMES_PWD)
        self.driver.find_element("id", "doLoginForTp").click()

    def check_vacancy(self, url: str) -> List[str]:
        data = []
        self.driver.get(url)
        for car_class in ["M1", "P1"]:
            # Car Class
            print("------", car_class, "-------")
            cc = Select(self.driver.find_element("id", "carClass"))
            deal_class = [
                option.get_attribute("value")
                for option in cc.options
            ]
            if car_class in deal_class:
                cc.select_by_value(car_class)
            else:
                print("No Deal:", car_class)
                continue
            # Equipment
            display = self.driver.find_element("id", "optionEqArea")
            if display.get_attribute("style") == "display: none;":
                self.driver.find_element("id", "useOptionEq").click()
                equipment = self.driver.find_element("id", "isExistsEquipment")
                equipment.find_elements("class name", "opEqVal")[0].click()
            # Start datetime
            start_date = Select(self.driver.find_element("id", "dateStart"))
            start_date.select_by_value("2023-02-18 00:00:00.0")
            start_hour = Select(self.driver.find_element("id", "hourStart"))
            start_hour.select_by_value("7")
            start_minute = Select(self.driver.find_element("id", "minuteStart"))
            start_minute.select_by_value("00")
            # End datetime
            end_date = Select(self.driver.find_element("id", "dateEnd"))
            end_date.select_by_value("2023-02-18 00:00:00.0")
            end_hour = Select(self.driver.find_element("id", "hourEnd"))
            end_hour.select_by_value("23")
            end_minute = Select(self.driver.find_element("id", "minuteEnd"))
            end_minute.select_by_value("00")
            # Submit
            self.driver.find_element("id", "doCheckForClass").click()
            # Check
            try:
                back = self.driver.find_element("id", "jumpInput")
                data.append(car_class + " : " + url)
                back.click()
                print("abailable")
            except:
                print("something wrong")
                continue
        return data


    def get_avail(self) -> List[List[str]]:
        """Get whether any place is vacancy on the date.

        Args:
            date_time (datetime.datetime): the required date

        Retruns:
            List[Tuple[str, str, str]]: availability list.
        """
        self.start()
        self.driver.find_element("id", "area4").click()
        station_list = self.driver.find_element("id", "station-list")
        tokyo = station_list.find_elements("css selector", ".entrylist.randc.area2")[0]
        links = tokyo.find_elements("class name", "reserve-btn")
        urls = []
        for link in links:
            a = link.find_elements("tag name", "a")[0]
            urls.append(a.get_attribute("href"))
        return [self.check_vacancy(url) for url in urls]


def main():
    with TimesCarShareSnow() as api:
        data = api.get_avail()
    for d in data:
        for dd in d:
            print(dd)


if __name__ == "__main__":
    main()
