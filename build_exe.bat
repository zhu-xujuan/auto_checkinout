@echo off
chcp 65001 >nul
echo ========================================
echo   実行ファイル作成スクリプト
echo ========================================
echo.

echo 必要なパッケージを確認しています...
pip install pyinstaller --quiet
echo.

echo 出勤用の実行ファイルを作成します...
pyinstaller --onefile --console --name 出勤 --icon=NONE main.py
echo.

echo 退勤用の実行ファイルを作成します...
pyinstaller --onefile --console --name 退勤 --icon=NONE main.py
echo.

echo ========================================
echo 配布用フォルダを作成しています...
echo ========================================

if not exist "配布用" mkdir 配布用
copy /Y dist\出勤.exe 配布用\
copy /Y dist\退勤.exe 配布用\
copy /Y config.json.sample 配布用\config.json
copy /Y create_shortcuts.bat 配布用\

echo.
echo ========================================
echo 作成完了！
echo ========================================
echo.
echo 配布用フォルダの内容:
echo - 配布用\出勤.exe              （ダブルクリックで出勤）
echo - 配布用\退勤.exe              （ダブルクリックで退勤）
echo - 配布用\config.json           （設定ファイル - 各自で編集）
echo - 配布用\create_shortcuts.bat  （デスクトップショートカット作成）
echo.
echo 【配布方法】
echo 1. 「配布用」フォルダごとコピーして配布
echo 2. 配布先で config.json を編集（ユーザー名・パスワード）
echo 3. create_shortcuts.bat を実行（デスクトップにショートカット作成）
echo 4. デスクトップの「出勤」「退勤」をクリック
echo.
pause

