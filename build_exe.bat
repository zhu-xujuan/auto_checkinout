@echo off
chcp 65001 >nul
echo ========================================
echo   実行ファイル作成スクリプト
echo ========================================
echo.

echo 出勤用の実行ファイルを作成します...
pyinstaller --onefile --noconsole --name 出勤 --add-data "config.json;." main.py -- 出勤
echo.

echo 退勤用の実行ファイルを作成します...
pyinstaller --onefile --noconsole --name 退勤 --add-data "config.json;." main.py -- 退勤
echo.

echo ========================================
echo 作成完了！
echo ========================================
echo.
echo 実行ファイルは dist フォルダ内にあります:
echo - dist\出勤.exe
echo - dist\退勤.exe
echo.
echo これらのファイルと config.json を一緒に配布してください。
echo.
pause

