import datetime
import os
import time
from typing import Dict, List, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

URL = "https://www.cm9.eprs.jp/shinagawa/web/index.jsp"

# 何をする: バドミントン・クロスミントン の value
PURPOSE_BADMINTON = "31000000_31010600"

# 何週先まで確認するか（今週 + 10 = 計11週）
WEEKS_AHEAD = 11

TARGET_DAY_LABELS = ("土曜", "日曜", "祝日")


class ShinagawaBadminton:
    def __init__(self, headless=False, interval=10):
        self.interval = interval
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        chrome_binary = os.getenv("CHROME_BINARY_PATH")
        if chrome_binary:
            options.binary_location = chrome_binary

        for arg in [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-dev-tools",
            "--no-zygote",
            "--remote-debugging-pipe",
            "--window-size=1280,1696",
        ]:
            options.add_argument(arg)

        chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
        chromedriver_port = int(os.getenv("CHROMEDRIVER_PORT", "9515"))
        service = Service(executable_path=chromedriver_path, port=chromedriver_port)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(interval)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()
        del self.driver

    def quit(self):
        self.driver.quit()

    def _js_click(self, element):
        """JavaScriptを使ってクリック（要素が隠れている場合に対応）"""
        self.driver.execute_script("arguments[0].click();", element)

    def _setup_common_conditions(self):
        """共通検索条件を設定する。
        - いつ: 今日
        - 曜日: 土・日・祝
        - 時間帯: 終日
        - 何をする: バドミントン・クロスミントン
        """
        # ページ読み込み
        self.driver.get(URL)
        time.sleep(2)

        # いつ: 今日 ラジオボタンを選択
        self._js_click(self.driver.find_element(By.ID, "today"))
        time.sleep(0.3)

        # 詳細条件（曜日・時間帯）を展開
        self._js_click(self.driver.find_element(By.ID, "collapse-when"))
        time.sleep(0.5)

        # 曜日: 土・日・祝 チェックボックスをON
        for day_id in ["saturday", "sunday", "holiday"]:
            self._js_click(self.driver.find_element(By.ID, day_id))
            time.sleep(0.2)

        # 時間帯: 終日
        self._js_click(self.driver.find_element(By.ID, "allday"))
        time.sleep(0.3)

        # 何をする: バドミントン・クロスミントン
        select_purpose = Select(self.driver.find_element(By.ID, "purpose"))
        select_purpose.select_by_value(PURPOSE_BADMINTON)
        time.sleep(0.3)

    def _get_bname_options(self) -> List[Tuple[str, str]]:
        """どこで（bname）の対象施設の選択肢を返す。

        Returns:
            List[Tuple[str, str]]: (value, text) のリスト
        """
        target_bnames = {"戸越体育館", "スクエア荏原"}
        select_bname = Select(self.driver.find_element(By.ID, "bname"))
        return [
            (opt.get_attribute("value"), opt.text)
            for opt in select_bname.options
            if opt.text in target_bnames
        ]

    def _ensure_search_form_visible(self):
        """検索フォームが表示された状態にする。
        結果ページにいる場合は「条件変更」ボタンで折りたたみを展開する。
        """
        if self.driver.current_url == URL:
            return
        # 結果ページ: 「条件変更」ボタンで free-search-cond を展開する
        try:
            self.driver.implicitly_wait(0)
            change_btn = self.driver.find_element(By.ID, "change-condition")
            cond_div = self.driver.find_element(By.ID, "free-search-cond")
            self.driver.implicitly_wait(self.interval)
            # collapse show クラスがなければ展開する
            cls = cond_div.get_attribute("class") or ""
            if "show" not in cls:
                self._js_click(change_btn)
                time.sleep(0.5)
        except Exception:
            self.driver.implicitly_wait(self.interval)
            # 何らかの問題があればページを再セットアップ
            self._setup_common_conditions()

    def _search_by_location(self, bname_value: str):
        """どこで を1つ選択して検索ボタンを押す。

        Args:
            bname_value (str): bname selectのvalue属性値
        """
        self._ensure_search_form_visible()
        # JS経由でselectのvalueを直接変更（非表示でも操作可能）
        self.driver.execute_script(
            "document.getElementById('bname').value = arguments[0];filterInst();",
            bname_value,
        )
        time.sleep(0.1)
        # トップページは btn-go、結果ページは btn-search
        btn_id = "btn-go" if self.driver.current_url == URL else "btn-search"
        self._js_click(self.driver.find_element(By.ID, btn_id))
        time.sleep(1)

    def _advance_week(self):
        """結果ページで翌週ボタンをクリックして次の週へ進む。"""
        self.driver.execute_script("document.getElementById('next-week').click();")
        time.sleep(1)

    def get_avail_all_locations(self) -> Dict[str, List[str]]:
        """どこで の施設を1つずつ選択して WEEKS_AHEAD 週分の空き情報を取得する。

        Returns:
            Dict[str, List[str]]: 施設名 -> 空き情報テキストのリスト
        """
        self._setup_common_conditions()
        bname_options = self._get_bname_options()

        results: Dict[str, List[str]] = {}

        for bname_value, bname_text in bname_options:
            # 前の施設で翌週へ進めているため、施設ごとに今日起点へ戻す
            self._setup_common_conditions()
            self._search_by_location(bname_value)

            # 今週から WEEKS_AHEAD 週分の結果を取得
            location_results: List[str] = []
            for week in range(WEEKS_AHEAD):
                location_results.extend(self._parse_result_page())
                if week < WEEKS_AHEAD - 1:
                    self._advance_week()

            if location_results:
                results[bname_text] = location_results
                print(f"[{bname_text}] {len(location_results)}件の空き")
                for r in location_results:
                    print(f"  {r}")
            else:
                print(f"[{bname_text}] 空きなし")

        return results

    def _parse_result_page(self) -> List[str]:
        """検索結果ページから空き情報テキストを取得する。

        空きセルは td.available.bg-green として描画される。
        ヘッダー行から日付、行ヘッダーから時間帯を取得する。

        Returns:
            List[str]: 空き情報の文字列リスト（例: "3月15日(日曜) 午前"）
        """
        avail_list = []
        try:
            self.driver.implicitly_wait(0)
            table = self.driver.find_element(By.ID, "week-info")
            self.driver.implicitly_wait(self.interval)
            # ヘッダー行から日付テキストを取得（列インデックス -> 日付文字列）
            header_cells = table.find_elements(By.XPATH, ".//thead/tr/th")
            # 0番目は「時間帯」ラベルなのでスキップ
            date_labels = []
            for th in header_cells[1:]:
                date_labels.append(th.text.replace("\n", " ").strip())

            # tbody の各行を処理
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            for row in rows:
                time_label = row.find_element(By.TAG_NAME, "th").text.strip()
                cells = row.find_elements(By.TAG_NAME, "td")
                for i, cell in enumerate(cells):
                    date_text = date_labels[i] if i < len(date_labels) else ""
                    if not any(label in date_text for label in TARGET_DAY_LABELS):
                        continue
                    cell_class = cell.get_attribute("class") or ""
                    if "available" in cell_class:
                        avail_list.append(f"{date_text} {time_label}".strip())
        except Exception:
            self.driver.implicitly_wait(self.interval)
        return avail_list


def main():
    # 今日から WEEKS_AHEAD 週分の空き情報を対象施設について取得
    today = datetime.datetime.now() + datetime.timedelta(hours=9)
    text = today.strftime(
        f"%Y年%m月%d日(%a) 今後{WEEKS_AHEAD}週間（土日祝）の空き情報"
    ) + "\n"
    print(text)

    with ShinagawaBadminton(headless=True) as api:
        results = api.get_avail_all_locations()

    print("\n=== 検索完了 ===")
    print(f"空きあり施設数: {len(results)}")
    print(results)
    return results


if __name__ == "__main__":
    main()
