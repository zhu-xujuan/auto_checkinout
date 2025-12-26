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
    echo   ※既に退勤済みの場合もこのメッセージが表示されます
) else (
    echo.
    echo ✗ 退勤処理に失敗しました。
    echo   ・まだ出勤していない場合：先に出勤してください
    echo   ・その他の場合：ログを確認してください
)

echo.
pause

