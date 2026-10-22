@echo off
chcp 65001 >nul
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"

if not exist "base\base_branded.exe" (
    echo [ERROR] base\base_branded.exe not found.
    echo See docs\BUILD.md for how to prepare the upstream base binary.
    pause
    exit /b 1
)

if not exist "assets\interface\home_Q.png" (
    echo [ERROR] assets\interface templates not found.
    echo See docs\BUILD.md for the required interface template files.
    pause
    exit /b 1
)

if not defined PYTHON set "PYTHON=py -3.11"
if not exist "build" mkdir "build"

echo [1/7] compile ui_compact.py
%PYTHON% scripts\compile_ui.py
if errorlevel 1 goto fail

echo.
echo [2/7] compile sound_library.py
%PYTHON% scripts\compile_sound_library.py
if errorlevel 1 goto fail

echo.
echo [3/7] generate detector.marshal
%PYTHON% scripts\patch_detector.py
if errorlevel 1 goto fail

echo.
echo [4/7] prepare V1.2.7 base
copy /Y "base\base_branded.exe" "build\base_v127.exe" >nul
if errorlevel 1 goto fail
%PYTHON% scripts\patch_version_info.py "build\base_v127.exe"
if errorlevel 1 goto fail

echo.
echo [5/7] repack PYZ
%PYTHON% scripts\repack_pyz.py "build\base_v127.exe" "build\_V1.2.7_full.exe"
if errorlevel 1 goto fail

echo.
echo [6/7] remove unused assets
%PYTHON% scripts\strip_embedded_assets.py "build\_V1.2.7_full.exe" "build\从零开始的塔科夫生活_V1.2.7.exe"
if errorlevel 1 goto fail

echo.
echo [7/7] validate output
%PYTHON% scripts\validate_final.py "build\从零开始的塔科夫生活_V1.2.7.exe"
if errorlevel 1 goto fail

echo.
echo Build complete: build\从零开始的塔科夫生活_V1.2.7.exe
pause
exit /b 0

:fail
echo.
echo Build failed. Check the error above.
pause
exit /b 1
