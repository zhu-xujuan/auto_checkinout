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
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# WebDriver Manager（自動ドライバーダウンロード）
try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.firefox.service import Service as FirefoxService

    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

# ベースディレクトリを取得（exe実行時も対応）
import os as _os

if getattr(sys, "frozen", False):
    _base_dir = Path(_os.path.dirname(sys.executable))
else:
    _base_dir = Path(_os.path.dirname(_os.path.abspath(__file__)))

# ログ設定
log_dir = _base_dir / "logs"
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
        self.base_dir = self._get_base_dir()
        self.config = self.load_config(config_path)
        self.driver = None

    def _get_base_dir(self):
        """実行ファイルのベースディレクトリを取得"""
        import os

        if getattr(sys, "frozen", False):
            # PyInstallerでビルドされた実行ファイルの場合
            return os.path.dirname(sys.executable)
        else:
            # 通常のPythonスクリプトの場合
            return os.path.dirname(os.path.abspath(__file__))

    def load_config(self, config_path):
        """設定ファイルを読み込む"""
        import os

        # 実行ファイルと同じディレクトリからconfig.jsonを探す
        full_path = os.path.join(self.base_dir, config_path)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"設定ファイルを読み込みました: {full_path}")
            return config
        except FileNotFoundError:
            logger.error(f"設定ファイル '{full_path}' が見つかりません")
            print(f"\nエラー: config.json が見つかりません")
            print(f"場所: {full_path}")
            print("\nconfig.json を実行ファイルと同じフォルダに配置してください。")
            input("Enterキーを押して終了...")
            sys.exit(1)
        except json.JSONDecodeError:
            logger.error("設定ファイルのJSON形式が正しくありません")
            print("\nエラー: config.json の形式が正しくありません")
            input("Enterキーを押して終了...")
            sys.exit(1)

    def setup_driver(self):
        """WebDriverをセットアップ（Chrome/Edge/Firefoxを自動検出）"""
        # 優先順位: config指定 > Chrome > Edge > Firefox
        browser_priority = self.config.get("browser", "auto")

        if browser_priority == "auto":
            browsers_to_try = ["chrome", "edge", "firefox"]
        else:
            browsers_to_try = [browser_priority]

        for browser in browsers_to_try:
            try:
                if browser == "chrome":
                    self.driver = self._setup_chrome()
                elif browser == "edge":
                    self.driver = self._setup_edge()
                elif browser == "firefox":
                    self.driver = self._setup_firefox()
                else:
                    continue

                if self.driver:
                    self.driver.implicitly_wait(10)
                    logger.info(f"{browser.capitalize()} WebDriverを起動しました")
                    return
            except Exception as e:
                logger.warning(f"{browser.capitalize()}の起動に失敗: {e}")
                continue

        logger.error("利用可能なブラウザが見つかりませんでした")
        sys.exit(1)

    def _setup_chrome(self):
        """Chrome WebDriverをセットアップ"""
        chrome_options = ChromeOptions()

        # ヘッドレスモードの設定（設定ファイルで変更可能）
        if self.config.get("headless", False):
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")

        # 基本オプション
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # 言語設定（日本語優先）
        chrome_options.add_argument("--lang=ja")
        chrome_options.add_argument("--accept-lang=ja,en-US,en")

        # 詳細設定（prefs）
        prefs = {
            # 通知を拒否
            "profile.default_content_setting_values.notifications": 2,
            # 位置情報を拒否
            "profile.default_content_setting_values.geolocation": 2,
            # カメラを拒否
            "profile.default_content_setting_values.media_stream_camera": 2,
            # マイクを拒否
            "profile.default_content_setting_values.media_stream_mic": 2,
            # パスワード保存を無効化
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            # 自動入力を無効化
            "autofill.profile_enabled": False,
            "autofill.credit_card_enabled": False,
            # Cookieを許可
            "profile.default_content_setting_values.cookies": 1,
            # ポップアップを許可
            "profile.default_content_setting_values.popups": 1,
            # ダウンロードプロンプトを表示
            "download.prompt_for_download": True,
            # 翻訳プロンプトを無効化
            "translate.enabled": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # 追加のオプション
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-translate")

        # ユーザーデータディレクトリの指定（オプション）
        if "user_data_dir" in self.config and self.config["user_data_dir"]:
            chrome_options.add_argument(f"user-data-dir={self.config['user_data_dir']}")

        if WEBDRIVER_MANAGER_AVAILABLE:
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=chrome_options)
        else:
            return webdriver.Chrome(options=chrome_options)

    def _setup_edge(self):
        """Edge WebDriverをセットアップ"""
        edge_options = EdgeOptions()

        # ヘッドレスモード
        if self.config.get("headless", False):
            edge_options.add_argument("--headless")
            edge_options.add_argument("--disable-gpu")

        # 基本オプション
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--disable-blink-features=AutomationControlled")

        # 言語設定（日本語優先）
        edge_options.add_argument("--lang=ja")
        edge_options.add_argument("--accept-lang=ja,en-US,en")

        # 詳細設定（prefs）
        prefs = {
            # 通知を拒否
            "profile.default_content_setting_values.notifications": 2,
            # 位置情報を拒否
            "profile.default_content_setting_values.geolocation": 2,
            # カメラを拒否
            "profile.default_content_setting_values.media_stream_camera": 2,
            # マイクを拒否
            "profile.default_content_setting_values.media_stream_mic": 2,
            # パスワード保存を無効化
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            # 自動入力を無効化
            "autofill.profile_enabled": False,
            "autofill.credit_card_enabled": False,
            # Cookieを許可
            "profile.default_content_setting_values.cookies": 1,
            # ポップアップを許可
            "profile.default_content_setting_values.popups": 1,
            # ダウンロードプロンプトを表示
            "download.prompt_for_download": True,
            # 翻訳プロンプトを無効化
            "translate.enabled": False,
        }
        edge_options.add_experimental_option("prefs", prefs)

        # 追加のオプション
        edge_options.add_argument("--disable-notifications")
        edge_options.add_argument("--disable-popup-blocking")
        edge_options.add_argument("--disable-infobars")
        edge_options.add_argument("--disable-translate")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option("useAutomationExtension", False)

        if WEBDRIVER_MANAGER_AVAILABLE:
            service = EdgeService(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=service, options=edge_options)
        else:
            return webdriver.Edge(options=edge_options)

    def _setup_firefox(self):
        """Firefox WebDriverをセットアップ"""
        firefox_options = FirefoxOptions()

        # ヘッドレスモード
        if self.config.get("headless", False):
            firefox_options.add_argument("--headless")

        # 言語設定（日本語優先）
        firefox_options.set_preference("intl.accept_languages", "ja,en-US,en")

        # 通知を拒否
        firefox_options.set_preference("dom.webnotifications.enabled", False)
        firefox_options.set_preference("dom.push.enabled", False)
        firefox_options.set_preference("permissions.default.desktop-notification", 2)

        # 位置情報を拒否
        firefox_options.set_preference("geo.enabled", False)
        firefox_options.set_preference("permissions.default.geo", 2)

        # カメラ・マイクを拒否
        firefox_options.set_preference("media.navigator.enabled", False)
        firefox_options.set_preference("media.navigator.permission.disabled", True)
        firefox_options.set_preference("permissions.default.camera", 2)
        firefox_options.set_preference("permissions.default.microphone", 2)

        # パスワード保存を無効化
        firefox_options.set_preference("signon.rememberSignons", False)
        firefox_options.set_preference("signon.autofillForms", False)

        # 自動入力を無効化
        firefox_options.set_preference("browser.formfill.enable", False)

        # Cookieを許可
        firefox_options.set_preference("network.cookie.cookieBehavior", 0)

        # ポップアップを許可
        firefox_options.set_preference("dom.disable_open_during_load", False)

        # ダウンロードプロンプトを表示
        firefox_options.set_preference("browser.download.useDownloadDir", False)
        firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "")

        # 翻訳プロンプトを無効化
        firefox_options.set_preference("browser.translations.enable", False)

        # その他の設定
        firefox_options.set_preference("browser.tabs.warnOnClose", False)
        firefox_options.set_preference("browser.shell.checkDefaultBrowser", False)

        if WEBDRIVER_MANAGER_AVAILABLE:
            service = FirefoxService(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=firefox_options)
        else:
            return webdriver.Firefox(options=firefox_options)

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

            # ページが完全に読み込まれるまで追加待機
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logger.info("ページの読み込みが完了しました")

            # TeamSpiritウィジェットの読み込みを待つ
            logger.info("TeamSpiritウィジェットの読み込みを待機中...")
            time.sleep(10)
            logger.info("追加待機が完了しました")

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

    def click_checkin_button(self, work_location=None):
        """出勤ボタンをクリック"""
        # 勤務場所が指定されている場合、先にタブをクリック
        if work_location:
            if not self._click_location_tab(work_location):
                logger.warning(
                    f"勤務場所「{work_location}」の選択に失敗しましたが、続行します"
                )

        return self._click_button("checkin", "出勤")

    def click_checkout_button(self, work_location=None):
        """退勤ボタンをクリック"""
        # 退勤前に出勤済みかチェック
        if not self._check_already_checked_in():
            logger.warning("まだ出勤していません。退勤処理をスキップします。")
            return "not_checked_in"

        # 勤務場所が指定されている場合、先にタブをクリック
        if work_location:
            if not self._click_location_tab(work_location):
                logger.warning(
                    f"勤務場所「{work_location}」の選択に失敗しましたが、続行します"
                )

        return self._click_button("checkout", "退勤")

    def _click_location_tab(self, location_name):
        """勤務場所タブをクリック（自宅、本社など）"""
        try:
            logger.info(f"勤務場所「{location_name}」タブを探しています...")

            # Shadow DOM内のiframeで探す
            try:
                js_code = """
                const alohaPage = document.querySelector('force-aloha-page');
                if (alohaPage && alohaPage.shadowRoot) {
                    const vfIframe = alohaPage.shadowRoot.querySelector('iframe[name^="vfFrameId"]');
                    return vfIframe;
                }
                return null;
                """
                vf_iframe = self.driver.execute_script(js_code)

                if vf_iframe:
                    self.driver.switch_to.frame(vf_iframe)
                    time.sleep(2)
            except Exception as e:
                logger.info(f"Shadow DOM探索: {e}")

            # タブ要素を探す（複数のセレクタで試行）
            tab_selectors = [
                f"//div[text()='{location_name}']",
                f"//span[text()='{location_name}']",
                f"//button[text()='{location_name}']",
                f"//*[contains(@class, 'tab') and text()='{location_name}']",
                f"//*[@role='tab' and text()='{location_name}']",
            ]

            for selector in tab_selectors:
                try:
                    tabs = self.driver.find_elements(By.XPATH, selector)
                    for tab in tabs:
                        if tab.text.strip() == location_name:
                            tab.click()
                            logger.info(
                                f"★ 勤務場所「{location_name}」タブをクリックしました"
                            )
                            time.sleep(2)
                            return True
                except:
                    continue

            # JavaScriptで探す
            js_find_tab = f"""
            const allElements = document.querySelectorAll('[class*="tab"], [role="tab"], button, div, span');
            for (const el of allElements) {{
                if (el.textContent.trim() === '{location_name}') {{
                    el.click();
                    return true;
                }}
            }}
            return false;
            """
            result = self.driver.execute_script(js_find_tab)
            if result:
                logger.info(
                    f"★ 勤務場所「{location_name}」タブをクリックしました（JS）"
                )
                time.sleep(2)
                return True

            logger.warning(f"勤務場所「{location_name}」タブが見つかりませんでした")
            return False

        except Exception as e:
            logger.error(f"勤務場所タブのクリック中にエラーが発生しました: {e}")
            return False

    def _check_already_checked_in(self):
        """出勤済みかどうかをチェック"""
        try:
            logger.info("出勤済みかどうかをチェックしています...")

            # 出勤ボタンを探す
            button_config = self.config["buttons"]["checkin"]
            selector_type = button_config["selector_type"]
            selector_value = button_config["selector_value"]

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

            # 出勤ボタンを探す（出勤ボタンのみを対象）
            checkin_button = self._find_button_in_frames(
                by_type, selector_value, target_button="出勤"
            )

            # 見つからなかった場合、IDで探す
            if checkin_button is None:
                checkin_button = self._find_button_by_id_everywhere("btnStInput")

            if checkin_button is None:
                logger.warning("出勤ボタンが見つからないため、出勤状態を確認できません")
                return False

            # ボタンが無効化されているかチェック（disabled="true"なら出勤済み）
            is_disabled = checkin_button.get_attribute("disabled")
            if is_disabled is not None:
                logger.info("✓ 出勤済みです")
                return True
            else:
                logger.warning("✗ まだ出勤していません")
                return False

        except Exception as e:
            logger.error(f"出勤状態のチェック中にエラーが発生しました: {e}")
            return False
        finally:
            # メインフレームに戻る
            try:
                self.driver.switch_to.default_content()
            except:
                pass

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

            # まずボタンの存在を確認（メインフレームとiframe）- target_buttonを指定
            button = self._find_button_in_frames(
                by_type, selector_value, target_button=button_name
            )

            # 見つからなかった場合、IDで直接探す（フォールバック）
            if button is None:
                logger.info(
                    f"{button_name}ボタンをIDで直接探します（フォールバック）..."
                )
                button_id = "btnStInput" if button_name == "出勤" else "btnEtInput"
                button = self._find_button_by_id_everywhere(button_id)

            if button is None:
                logger.error(
                    f"{button_name}ボタンが見つかりませんでした（タイムアウト）"
                )
                return False

            # ボタンが無効化されているかチェック（既に押された状態）
            is_disabled = button.get_attribute("disabled")
            if is_disabled is not None:
                logger.info(f"既に{button_name}済みです")
                return "already_done"

            # ボタンをクリック
            try:
                button.click()
                logger.info(f"{button_name}ボタンをクリックしました")
                time.sleep(3)
                return True
            except Exception as e:
                # JavaScriptでクリックを試行
                logger.info("JavaScriptでクリックを試行します...")
                self.driver.execute_script("arguments[0].click();", button)
                logger.info(f"{button_name}ボタンをクリックしました")
                time.sleep(3)
                return True

        except Exception as e:
            logger.error(f"{button_name}ボタンのクリック中にエラーが発生しました: {e}")
            return False

    def _find_button_in_frames(self, by_type, selector_value, target_button=None):
        """メインフレームとすべてのiframe内でボタンを探す

        Args:
            by_type: Byタイプ
            selector_value: セレクター値
            target_button: 探しているボタン名（"出勤" または "退勤"）。Noneの場合は両方対象
        """

        # target_buttonに対応するIDを決定
        if target_button == "出勤":
            target_ids = ["btnStInput"]
            target_values = ["出勤"]
        elif target_button == "退勤":
            target_ids = ["btnEtInput"]
            target_values = ["退勤"]
        else:
            target_ids = ["btnStInput", "btnEtInput"]
            target_values = ["出勤", "退勤"]

        # まずShadow DOM内のiframeを探す（TeamSpirit/Salesforce Lightning対応）
        try:
            logger.info("Shadow DOM内のVisualforce iframeを探しています...")
            button = self._find_button_in_shadow_dom(
                by_type, selector_value, target_button
            )
            if button:
                return button
        except Exception as e:
            logger.info(f"Shadow DOM探索: {e}")

        # メインフレームで探す（詳細チェック）
        try:
            logger.info("メインフレームでボタンを探しています...")

            # まず詳細にすべての要素を確認
            logger.info("メインフレームの全要素をチェック中...")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.info(
                f"メインフレーム: {len(inputs)}個のinput要素、{len(buttons)}個のbutton要素"
            )

            # 指定されたボタンのみを探す
            for idx, elem in enumerate(inputs + buttons):
                try:
                    elem_id = elem.get_attribute("id")
                    elem_value = elem.get_attribute("value")
                    elem_text = elem.text
                    if (
                        elem_value in target_values
                        or elem_text in target_values
                        or elem_id in target_ids
                    ):
                        logger.info(
                            f"★メインフレームでボタン発見: id={elem_id}, value={elem_value}, text={elem_text}"
                        )
                        return elem
                except:
                    pass

            # XPathで再度探す
            button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((by_type, selector_value))
            )
            logger.info("メインフレームでボタンを発見しました")
            return button
        except TimeoutException:
            logger.info("メインフレームにボタンが見つかりませんでした")

        # iframe内を探す
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        logger.info(f"{len(iframes)}個のiframeが見つかりました")

        for i, iframe in enumerate(iframes):
            try:
                logger.info(f"iframe[{i}]でボタンを探しています...")
                self.driver.switch_to.frame(iframe)

                # iframe内のbody要素が読み込まれるまで待機
                try:
                    logger.info(f"iframe[{i}]のbody要素の読み込みを待機中...")
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    logger.info(f"iframe[{i}]のbody要素が読み込まれました")
                except Exception as e:
                    logger.warning(f"iframe[{i}]のbody読み込み待機エラー: {e}")

                # デバッグ: iframe内のinputボタンをすべてリスト
                try:
                    # TeamSpiritウィジェットの読み込みを待つ（動的読み込み対応）
                    logger.info("iframe内のコンテンツ読み込みを待機中...")
                    max_wait = 60  # 最大60秒待機（30秒→60秒に延長）
                    wait_interval = 5  # 5秒ごとにチェック（3秒→5秒に延長）
                    button_found = False

                    for attempt in range(max_wait // wait_interval):
                        time.sleep(wait_interval)

                        # inputタグとbuttonタグの両方を探す
                        inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        all_elements = inputs + buttons

                        logger.info(
                            f"iframe[{i}]内に{len(inputs)}個のinput要素、{len(buttons)}個のbutton要素が見つかりました（{attempt + 1}回目のチェック）"
                        )

                        # すべての要素をチェック
                        for idx, elem in enumerate(all_elements):
                            try:
                                elem_id = elem.get_attribute("id")
                                elem_type = elem.get_attribute("type")
                                elem_value = elem.get_attribute("value")
                                elem_text = elem.text
                                elem_class = elem.get_attribute("class")

                                # 出勤または退勤ボタンを発見
                                if elem_value in ["出勤", "退勤"] or elem_text in [
                                    "出勤",
                                    "退勤",
                                ]:
                                    logger.info(
                                        f"  ★ボタン発見[{idx}]: id={elem_id}, type={elem_type}, value={elem_value}, text={elem_text}, class={elem_class}"
                                    )
                                    button_found = True
                                else:
                                    # すべての要素をログ出力（type=buttonは必ず出力）
                                    if elem_type == "button" or idx < 30:
                                        logger.info(
                                            f"  要素[{idx}]: id={elem_id}, type={elem_type}, value={elem_value}, text={elem_text}"
                                        )
                            except:
                                pass

                        if button_found:
                            logger.info(f"iframe[{i}]内で出勤/退勤ボタンを発見しました")
                            break

                    if not button_found:
                        logger.warning(
                            f"iframe[{i}]内に出勤/退勤ボタンが見つかりませんでした（{max_wait}秒待機後）"
                        )
                except Exception as debug_e:
                    logger.warning(f"デバッグ情報取得エラー: {debug_e}")

                button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by_type, selector_value))
                )
                logger.info(f"iframe[{i}]でボタンを発見しました")
                return button

            except TimeoutException:
                logger.info(f"iframe[{i}]にボタンが見つかりませんでした")
                self.driver.switch_to.default_content()
                continue
            except Exception as e:
                logger.warning(f"iframe[{i}]のチェック中にエラー: {e}")
                self.driver.switch_to.default_content()
                continue

        # すべてのフレームで見つからなかった
        self.driver.switch_to.default_content()
        return None

    def _find_button_in_shadow_dom(self, by_type, selector_value, target_button=None):
        """Shadow DOM内のVisualforce iframe内でボタンを探す（TeamSpirit/Salesforce Lightning対応）

        Args:
            by_type: Byタイプ
            selector_value: セレクター値
            target_button: 探しているボタン名（"出勤" または "退勤"）。Noneの場合は両方対象
        """
        try:
            logger.info("force-aloha-page のShadow DOMを探索中...")

            # target_buttonに対応するIDと値を決定
            if target_button == "出勤":
                target_ids = ["btnStInput"]
                target_values = ["出勤"]
            elif target_button == "退勤":
                target_ids = ["btnEtInput"]
                target_values = ["退勤"]
            else:
                target_ids = ["btnStInput", "btnEtInput"]
                target_values = ["出勤", "退勤"]

            # JavaScriptでShadow DOM内のiframeを取得
            js_code = """
            // force-aloha-pageのShadow Root内のiframeを取得
            const alohaPage = document.querySelector('force-aloha-page');
            if (!alohaPage || !alohaPage.shadowRoot) {
                return null;
            }
            
            // Shadow root内のVisualforce iframeを取得
            const vfIframe = alohaPage.shadowRoot.querySelector('iframe[name^="vfFrameId"]');
            return vfIframe;
            """

            vf_iframe = self.driver.execute_script(js_code)

            if vf_iframe:
                logger.info("★ Visualforce iframe (Shadow DOM内) を発見しました！")

                # iframeに切り替え
                self.driver.switch_to.frame(vf_iframe)
                logger.info("Visualforce iframeに切り替えました")

                # iframe内のコンテンツが読み込まれるまで待機
                time.sleep(5)

                # ボタンを探す
                logger.info(
                    f"iframe内で{target_button or '出勤/退勤'}ボタンを探しています..."
                )

                # 複数のセレクタで検索（target_buttonに応じて絞り込み）
                button_selectors = []
                for btn_id in target_ids:
                    button_selectors.append((By.ID, btn_id))
                for btn_value in target_values:
                    button_selectors.append(
                        (By.XPATH, f"//input[@type='button' and @value='{btn_value}']")
                    )
                    button_selectors.append(
                        (By.CSS_SELECTOR, f"input[value='{btn_value}']")
                    )

                # まず指定されたセレクタで探す
                try:
                    button = self.driver.find_element(by_type, selector_value)
                    btn_value = button.get_attribute("value")
                    if btn_value in target_values:
                        logger.info(
                            f"★ Shadow DOM内のiframeで{target_button or btn_value}ボタンを発見しました！"
                        )
                        return button
                except:
                    pass

                # 代替セレクタで探す
                for sel_by, sel_value in button_selectors:
                    try:
                        button = self.driver.find_element(sel_by, sel_value)
                        btn_id = button.get_attribute("id")
                        btn_value = button.get_attribute("value")
                        if btn_id in target_ids or btn_value in target_values:
                            logger.info(
                                f"★ Shadow DOM内のiframeでボタンを発見: id={btn_id}, value={btn_value}"
                            )
                            return button
                    except:
                        continue

                # デバッグ: iframe内の全要素をログに出力
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                logger.info(f"Shadow DOM iframe内: {len(inputs)}個のinput要素")
                for idx, inp in enumerate(inputs[:30]):
                    try:
                        inp_id = inp.get_attribute("id")
                        inp_type = inp.get_attribute("type")
                        inp_value = inp.get_attribute("value")
                        logger.info(
                            f"  input[{idx}]: id={inp_id}, type={inp_type}, value={inp_value}"
                        )
                        if inp_value in target_values:
                            logger.info(f"★ {inp_value}ボタンを発見！")
                            return inp
                    except:
                        pass

                logger.info("Shadow DOM内のiframeにボタンが見つかりませんでした")
                self.driver.switch_to.default_content()
            else:
                logger.info("force-aloha-page または Shadow DOM が見つかりませんでした")

            return None

        except Exception as e:
            logger.warning(f"Shadow DOM探索中にエラー: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return None

    def _find_button_by_id_everywhere(self, button_id):
        """IDを使ってメインフレームとすべてのiframe内でボタンを探す"""
        logger.info(f"ID '{button_id}' でボタンを探索開始...")

        # まずShadow DOM内を探す
        try:
            logger.info("Shadow DOM内でIDを検索中...")
            js_code = """
            const alohaPage = document.querySelector('force-aloha-page');
            if (alohaPage && alohaPage.shadowRoot) {
                const vfIframe = alohaPage.shadowRoot.querySelector('iframe[name^="vfFrameId"]');
                return vfIframe;
            }
            return null;
            """
            vf_iframe = self.driver.execute_script(js_code)

            if vf_iframe:
                logger.info("★ Shadow DOM内のVisualforce iframeを発見")
                self.driver.switch_to.frame(vf_iframe)
                time.sleep(3)

                button = self.driver.find_element(By.ID, button_id)
                logger.info(f"★ Shadow DOM内でID '{button_id}' のボタンを発見しました")
                return button
        except Exception as e:
            logger.info(f"Shadow DOM内でIDが見つかりませんでした: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass

        # メインフレームで探す
        try:
            self.driver.switch_to.default_content()
            button = self.driver.find_element(By.ID, button_id)
            logger.info(f"★メインフレームでID '{button_id}' のボタンを発見しました")
            return button
        except:
            pass

        # すべてのiframeで探す
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for i, iframe in enumerate(iframes):
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(iframe)

                # iframe内のbody要素が読み込まれるまで待機
                logger.info(f"iframe[{i}]のbody要素の読み込みを待機中...")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # さらに動的コンテンツの読み込みを待つ
                time.sleep(5)
                logger.info(f"iframe[{i}]のコンテンツ読み込み完了")

                button = self.driver.find_element(By.ID, button_id)
                logger.info(f"★iframe[{i}]でID '{button_id}' のボタンを発見しました")
                return button
            except Exception as e:
                logger.info(f"iframe[{i}]でボタンが見つかりませんでした: {e}")
                continue

        self.driver.switch_to.default_content()
        logger.warning(f"ID '{button_id}' のボタンはどこにも見つかりませんでした")
        return None

    def take_screenshot(self, filename):
        """スクリーンショットを保存"""
        try:
            screenshot_dir = Path(self.base_dir) / "screenshots"
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

    def execute(self, action_type, work_location=None):
        """出勤または退勤を実行

        Args:
            action_type: "出勤" または "退勤"
            work_location: 勤務場所（"自宅" など）。Noneの場合は選択しない
        """
        try:
            location_info = f"（{work_location}）" if work_location else ""
            logger.info(f"{'='*50}")
            logger.info(f"{action_type}{location_info}処理を開始します")
            logger.info(f"{'='*50}")

            # WebDriverセットアップ
            self.setup_driver()

            # ログイン
            if not self.login():
                self.take_screenshot(f"{action_type}_login_failed")
                return False

            # 出勤または退勤
            if action_type == "出勤":
                result = self.click_checkin_button(work_location)
            elif action_type == "退勤":
                result = self.click_checkout_button(work_location)
            else:
                logger.error(f"不正なアクションタイプ: {action_type}")
                return False

            # 結果に応じた処理
            if result == "already_done":
                # 既に出勤/退勤済みの場合
                self.take_screenshot(f"{action_type}_already_done")
                logger.info(f"既に{action_type}済みです。処理を完了します。")
                success = True
            elif result == "not_checked_in":
                # まだ出勤していない場合（退勤時のみ）
                self.take_screenshot(f"{action_type}_not_checked_in")
                logger.error("まだ出勤していません。先に出勤してください。")
                success = False
            elif result:
                # 成功した場合
                self.take_screenshot(f"{action_type}_success")
                logger.info(f"{action_type}処理が完了しました！")
                success = True
            else:
                # 失敗した場合
                self.take_screenshot(f"{action_type}_failed")
                logger.error(f"{action_type}処理に失敗しました")
                success = False

            # 結果確認のため少し待機
            time.sleep(3)

            return success

        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}")
            self.take_screenshot(f"{action_type}_error")
            return False
        finally:
            # メインフレームに戻る
            try:
                self.driver.switch_to.default_content()
            except:
                pass

            # 自動クローズの設定確認
            if self.config.get("auto_close", True):
                self.close()
            else:
                logger.info("ブラウザは開いたままです（auto_close=false）")


def main():
    """メイン処理"""
    import os

    # 実行ファイル名から動作を自動判断
    exe_name = os.path.basename(sys.argv[0])
    action_type = None
    work_location = None

    if len(sys.argv) >= 2:
        # コマンドライン引数がある場合
        action_type = sys.argv[1]
        if len(sys.argv) >= 3:
            work_location = sys.argv[2]  # 勤務場所（例: 自宅）
    else:
        # 実行ファイル名から判断
        if "在宅出勤" in exe_name:
            action_type = "出勤"
            work_location = "自宅"
            print("在宅出勤処理を開始します...")
        elif "在宅退勤" in exe_name:
            action_type = "退勤"
            work_location = "自宅"
            print("在宅退勤処理を開始します...")
        elif "出勤" in exe_name:
            action_type = "出勤"
            work_location = "恵比寿本社"
            print("出勤処理を開始します（恵比寿本社）...")
        elif "退勤" in exe_name:
            action_type = "退勤"
            work_location = "恵比寿本社"
            print("退勤処理を開始します（恵比寿本社）...")
        else:
            print("使用方法: python main.py [出勤|退勤] [勤務場所]")
            print("例: python main.py 出勤 自宅")
            print(
                "または: 出勤.exe / 退勤.exe / 在宅出勤.exe / 在宅退勤.exe をダブルクリック"
            )
            input("Enterキーを押して終了...")
            sys.exit(1)

    if action_type not in ["出勤", "退勤"]:
        print("エラー: 引数は '出勤' または '退勤' を指定してください")
        input("Enterキーを押して終了...")
        sys.exit(1)

    automation = SalesforceAutoCheckInOut()
    success = automation.execute(action_type, work_location)

    # 結果表示
    location_info = f"（{work_location}）" if work_location else ""
    if success:
        print(f"\n✓ {action_type}{location_info}処理が完了しました！")
    else:
        print(
            f"\n✗ {action_type}{location_info}処理に失敗しました。ログを確認してください。"
        )

    input("Enterキーを押して終了...")

    # 終了コード
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
