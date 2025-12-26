#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Salesforce 自動出勤・退勤システム
"""

import json
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ログ設定
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"auto_checkinout_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SalesforceAutoCheckInOut:
    """Salesforce自動出勤・退勤クラス"""

    def __init__(self, config_path="config.json"):
        """初期化"""
        self.config = self.load_config(config_path)
        self.driver = None

    def load_config(self, config_path):
        """設定ファイルを読み込む"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info("設定ファイルを読み込みました")
            return config
        except FileNotFoundError:
            logger.error(f"設定ファイル '{config_path}' が見つかりません")
            sys.exit(1)
        except json.JSONDecodeError:
            logger.error("設定ファイルのJSON形式が正しくありません")
            sys.exit(1)

    def setup_driver(self):
        """Chrome WebDriverをセットアップ"""
        try:
            chrome_options = Options()

            # ヘッドレスモードの設定（設定ファイルで変更可能）
            if self.config.get("headless", False):
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")

            # その他のオプション
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"]
            )
            chrome_options.add_experimental_option("useAutomationExtension", False)

            # ユーザーデータディレクトリの指定（オプション）
            if "user_data_dir" in self.config and self.config["user_data_dir"]:
                chrome_options.add_argument(
                    f"user-data-dir={self.config['user_data_dir']}"
                )

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("Chrome WebDriverを起動しました")

        except Exception as e:
            logger.error(f"WebDriverの起動に失敗しました: {e}")
            sys.exit(1)

    def login(self):
        """Salesforceにログイン"""
        try:
            logger.info("Salesforceにアクセスします...")
            self.driver.get(self.config["salesforce_url"])

            # ログインページの読み込み待機
            time.sleep(2)

            # ユーザー名入力
            logger.info("ユーザー名を入力します...")
            username_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(self.config["username"])

            # パスワード入力
            logger.info("パスワードを入力します...")
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.config["password"])

            # ログインボタンをクリック
            logger.info("ログインボタンをクリックします...")
            login_button = self.driver.find_element(By.ID, "Login")
            login_button.click()

            # ログイン後のページ読み込み待機
            time.sleep(5)
            logger.info("ログインに成功しました")

            return True

        except TimeoutException:
            logger.error("ログイン画面の読み込みがタイムアウトしました")
            return False
        except NoSuchElementException as e:
            logger.error(f"ログイン要素が見つかりません: {e}")
            return False
        except Exception as e:
            logger.error(f"ログイン中にエラーが発生しました: {e}")
            return False

    def click_checkin_button(self):
        """出勤ボタンをクリック"""
        return self._click_button("checkin", "出勤")

    def click_checkout_button(self):
        """退勤ボタンをクリック"""
        return self._click_button("checkout", "退勤")

    def _click_button(self, button_type, button_name):
        """指定されたボタンをクリック"""
        try:
            button_config = self.config["buttons"][button_type]
            selector_type = button_config["selector_type"]
            selector_value = button_config["selector_value"]

            logger.info(f"{button_name}ボタンを探しています...")

            # セレクタータイプに応じて要素を検索
            by_type_map = {
                "id": By.ID,
                "name": By.NAME,
                "class": By.CLASS_NAME,
                "xpath": By.XPATH,
                "css": By.CSS_SELECTOR,
                "link_text": By.LINK_TEXT,
                "partial_link_text": By.PARTIAL_LINK_TEXT,
            }

            by_type = by_type_map.get(selector_type.lower())
            if not by_type:
                logger.error(f"不正なセレクタータイプ: {selector_type}")
                return False

            # ボタンをクリック
            button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((by_type, selector_value))
            )
            button.click()

            logger.info(f"{button_name}ボタンをクリックしました")
            time.sleep(3)

            return True

        except TimeoutException:
            logger.error(f"{button_name}ボタンが見つかりませんでした（タイムアウト）")
            return False
        except Exception as e:
            logger.error(f"{button_name}ボタンのクリック中にエラーが発生しました: {e}")
            return False

    def take_screenshot(self, filename):
        """スクリーンショットを保存"""
        try:
            screenshot_dir = Path("screenshots")
            screenshot_dir.mkdir(exist_ok=True)
            filepath = (
                screenshot_dir
                / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            self.driver.save_screenshot(str(filepath))
            logger.info(f"スクリーンショットを保存しました: {filepath}")
        except Exception as e:
            logger.error(f"スクリーンショットの保存に失敗しました: {e}")

    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")

    def execute(self, action_type):
        """出勤または退勤を実行"""
        try:
            logger.info(f"{'='*50}")
            logger.info(f"{action_type}処理を開始します")
            logger.info(f"{'='*50}")

            # WebDriverセットアップ
            self.setup_driver()

            # ログイン
            if not self.login():
                self.take_screenshot(f"{action_type}_login_failed")
                return False

            # 出勤または退勤
            if action_type == "出勤":
                success = self.click_checkin_button()
            elif action_type == "退勤":
                success = self.click_checkout_button()
            else:
                logger.error(f"不正なアクションタイプ: {action_type}")
                return False

            if success:
                self.take_screenshot(f"{action_type}_success")
                logger.info(f"{action_type}処理が完了しました！")
            else:
                self.take_screenshot(f"{action_type}_failed")
                logger.error(f"{action_type}処理に失敗しました")

            # 結果確認のため少し待機
            time.sleep(3)

            return success

        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}")
            self.take_screenshot(f"{action_type}_error")
            return False
        finally:
            # 自動クローズの設定確認
            if self.config.get("auto_close", True):
                self.close()
            else:
                logger.info("ブラウザは開いたままです（auto_close=false）")


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python main.py [出勤|退勤]")
        sys.exit(1)

    action_type = sys.argv[1]

    if action_type not in ["出勤", "退勤"]:
        print("エラー: 引数は '出勤' または '退勤' を指定してください")
        sys.exit(1)

    automation = SalesforceAutoCheckInOut()
    success = automation.execute(action_type)

    # 終了コード
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
