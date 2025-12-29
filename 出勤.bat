@echo off
chcp 65001 >nul
echo ========================================
echo   Salesforce 自動出勤システム（恵比寿本社）
echo ========================================
echo.
echo 出勤処理を開始します...
echo.

python main.py 出勤 恵比寿本社

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ 出勤処理が完了しました！
    echo   ※既に出勤済みの場合もこのメッセージが表示されます
) else (
    echo.
    echo ✗ 出勤処理に失敗しました。ログを確認してください。
)

echo.
pause

