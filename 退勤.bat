@echo off
chcp 65001 >nul
echo ========================================
echo   Salesforce 自動退勤システム
echo ========================================
echo.
echo 退勤処理を開始します...
echo.

python main.py 退勤

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ 退勤処理が完了しました！
) else (
    echo.
    echo ✗ 退勤処理に失敗しました。ログを確認してください。
)

echo.
pause

