@echo off
chcp 65001 > nul
echo ========================================
echo   Salesforce 在宅退勤処理
echo ========================================
echo.

cd /d %~dp0

python main.py 退勤 自宅

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ★ 在宅退勤処理が正常に完了しました！
) else (
    echo.
    echo ✗ 在宅退勤処理に失敗しました。ログを確認してください。
)

pause

