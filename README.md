# Salesforce 自動出勤・退勤システム

Salesforceへの出勤・退勤を自動化するPythonスクリプトです。

## 📋 必要な環境

### 開発環境があるPCの場合
- Python 3.8以上
- Chrome ブラウザ
- ChromeDriver（自動インストール対応）

### 開発環境がないPCの場合
- Chrome ブラウザのみ
- 実行ファイル（.exe）を使用

## 🚀 セットアップ手順

### 1. 開発環境でのセットアップ

```bash
# 1. 必要なライブラリをインストール
pip install -r requirements.txt

# 2. config.jsonを編集して設定を行う
# （詳細は下記の「設定方法」を参照）
```

### 2. 設定方法

`config.json` ファイルを編集してください：

```json
{
  "salesforce_url": "https://login.salesforce.com/",
  "username": "あなたのメールアドレス",
  "password": "あなたのパスワード",
  "buttons": {
    "checkin": {
      "selector_type": "xpath",
      "selector_value": "//button[contains(text(), '出勤')]"
    },
    "checkout": {
      "selector_type": "xpath",
      "selector_value": "//button[contains(text(), '退勤')]"
    }
  }
}
```

#### 必要な入力情報

1. **salesforce_url**: SalesforceのログインURL
   - 例: `https://login.salesforce.com/`
   - カスタムドメインの場合: `https://yourcompany.my.salesforce.com/`

2. **username**: ログイン用のメールアドレス

3. **password**: ログイン用のパスワード

4. **buttons.checkin.selector_value**: 出勤ボタンの識別方法
   - 例（テキストで検索）: `//button[contains(text(), '出勤')]`
   - 例（IDで検索）: `checkin-button`（selector_typeをidに変更）

5. **buttons.checkout.selector_value**: 退勤ボタンの識別方法
   - 例（テキストで検索）: `//button[contains(text(), '退勤')]`

#### ボタンの識別方法の確認手順

1. Chrome で Salesforce にログイン
2. 出勤/退勤画面を開く
3. F12キーを押して開発者ツールを開く
4. 左上の要素選択ツール（矢印アイコン）をクリック
5. 出勤または退勤ボタンをクリック
6. 右側に表示されるHTMLから以下を確認：
   - `id="xxx"` があれば、selector_type を "id"、selector_value を "xxx" に設定
   - ボタンのテキストで検索する場合は、selector_type を "xpath"、selector_value を `//button[contains(text(), 'ボタンのテキスト')]` に設定

### 利用可能なセレクタータイプ

- `id`: 要素のID属性
- `name`: 要素のname属性
- `class`: 要素のclass名
- `xpath`: XPath式
- `css`: CSSセレクター
- `link_text`: リンクの完全一致テキスト
- `partial_link_text`: リンクの部分一致テキスト

## 📖 使用方法

### 開発環境がある場合

#### 方法1: バッチファイルをダブルクリック
- `出勤.bat` をダブルクリック → 出勤処理
- `退勤.bat` をダブルクリック → 退勤処理

#### 方法2: コマンドラインから実行
```bash
# 出勤
python main.py 出勤

# 退勤
python main.py 退勤
```

### 開発環境がない場合（実行ファイルの作成）

#### 実行ファイル（.exe）の作成手順

```bash
# build_exe.bat を実行
build_exe.bat
```

実行後、`dist` フォルダ内に以下のファイルが生成されます：
- `出勤.exe`: 出勤用実行ファイル
- `退勤.exe`: 退勤用実行ファイル

#### 配布方法

1. `dist` フォルダ内の以下をコピーして配布：
   - `出勤.exe`
   - `退勤.exe`
   - `config.json`（各自で編集してもらう）

2. 配布先のPCでの使用方法：
   - `config.json` を編集（ユーザー名・パスワードを設定）
   - `出勤.exe` または `退勤.exe` をダブルクリック

## 📁 フォルダ構成

```
auto_checkinout/
├── main.py                    # メインスクリプト
├── config.json               # 設定ファイル
├── 出勤.bat                  # ワンクリック出勤用
├── 退勤.bat                  # ワンクリック退勤用
├── requirements.txt          # 必要なライブラリ
├── build_exe.bat            # 実行ファイル化用スクリプト
├── README.md                # このファイル
├── logs/                    # ログファイル（自動生成）
└── screenshots/             # スクリーンショット（自動生成）
```

## 🔧 高度な設定

### config.json の追加オプション

```json
{
  "headless": false,
  "auto_close": true,
  "user_data_dir": ""
}
```

- **headless**: `true` にするとブラウザを表示せずに実行
- **auto_close**: `false` にすると処理後もブラウザを開いたまま
- **user_data_dir**: Chromeのユーザーデータディレクトリを指定（ログイン状態の保持など）

## 📝 ログとスクリーンショット

- **ログファイル**: `logs/auto_checkinout_YYYYMMDD.log`
  - 実行ログが日付ごとに保存されます
  
- **スクリーンショット**: `screenshots/`
  - 成功時・失敗時に自動的にスクリーンショットが保存されます

## ⚠️ トラブルシューティング

### 「ChromeDriverが見つかりません」エラー

1. Chrome ブラウザが最新版か確認
2. 以下のコマンドで手動インストール：
   ```bash
   pip install webdriver-manager
   ```

### ログインできない

1. `config.json` のユーザー名・パスワードが正しいか確認
2. `headless` を `false` にして、ブラウザの動作を目視確認
3. 2要素認証が有効になっている場合は無効化が必要

### ボタンが見つからない

1. `screenshots` フォルダのスクリーンショットを確認
2. F12 開発者ツールでボタンの要素を再確認
3. `config.json` の selector_value を調整

### 実行ファイルが起動しない

1. Chromeブラウザがインストールされているか確認
2. `config.json` が同じフォルダにあるか確認
3. ウイルス対策ソフトがブロックしていないか確認

## 🔒 セキュリティに関する注意

- `config.json` にはパスワードが平文で保存されます
- 他人と共有しないよう注意してください
- より安全な方法として、環境変数やキーチェーンの使用も検討できます

## 📄 ライセンス

このプロジェクトは個人利用・社内利用を目的としています。

## 🤝 サポート

問題が発生した場合は、`logs` フォルダのログファイルを確認してください。

