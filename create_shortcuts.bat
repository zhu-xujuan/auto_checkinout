@echo off
chcp 65001 >nul
echo ========================================
echo   デスクトップショートカット作成
echo ========================================
echo.

:: 現在のディレクトリを取得
set "CURRENT_DIR=%~dp0"

:: デスクトップのパスを取得
set "DESKTOP=%USERPROFILE%\Desktop"

:: 出勤ショートカットを作成
echo 出勤ショートカットを作成しています...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\出勤.lnk'); $s.TargetPath = '%CURRENT_DIR%出勤.exe'; $s.WorkingDirectory = '%CURRENT_DIR%'; $s.Description = 'Salesforce 自動出勤'; $s.Save()"

:: 退勤ショートカットを作成
echo 退勤ショートカットを作成しています...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\退勤.lnk'); $s.TargetPath = '%CURRENT_DIR%退勤.exe'; $s.WorkingDirectory = '%CURRENT_DIR%'; $s.Description = 'Salesforce 自動退勤'; $s.Save()"

:: 在宅出勤ショートカットを作成
echo 在宅出勤ショートカットを作成しています...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\在宅出勤.lnk'); $s.TargetPath = '%CURRENT_DIR%在宅出勤.exe'; $s.WorkingDirectory = '%CURRENT_DIR%'; $s.Description = 'Salesforce 自動在宅出勤'; $s.Save()"

:: 在宅退勤ショートカットを作成
echo 在宅退勤ショートカットを作成しています...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\在宅退勤.lnk'); $s.TargetPath = '%CURRENT_DIR%在宅退勤.exe'; $s.WorkingDirectory = '%CURRENT_DIR%'; $s.Description = 'Salesforce 自動在宅退勤'; $s.Save()"

echo.
echo ========================================
echo ショートカット作成完了！
echo ========================================
echo.
echo デスクトップに以下のショートカットを作成しました:
echo - 出勤.lnk      （通常の出勤）
echo - 退勤.lnk      （通常の退勤）
echo - 在宅出勤.lnk  （自宅タブ選択後に出勤）
echo - 在宅退勤.lnk  （自宅タブ選択後に退勤）
echo.
pause

