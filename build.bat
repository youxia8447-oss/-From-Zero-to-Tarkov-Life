@echo off
chcp 65001 >nul
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

echo [1/6] generate sound_library.marshal
%PYTHON% scripts\patch_sound_library.py
if errorlevel 1 goto fail

echo.
echo [2/6] prepare V1.2.2 base
if not exist "build" mkdir "build"
copy /Y "base\base_branded.exe" "build\base_v122.exe" >nul
if errorlevel 1 goto fail
%PYTHON% scripts\patch_version_info.py "build\base_v122.exe"
if errorlevel 1 goto fail

echo.
echo [3/6] compile ui_compact.py
%PYTHON% scripts\compile_ui.py
if errorlevel 1 goto fail

echo.
echo [4/6] generate detector.marshal
%PYTHON% scripts\patch_detector.py
if errorlevel 1 goto fail

echo.
echo [5/6] repack PYZ
%PYTHON% scripts\repack_pyz.py "build\base_v122.exe" "build\从零开始的塔科夫生活_V1.2.2.exe"
if errorlevel 1 goto fail

echo.
echo [6/6] validate output
%PYTHON% scripts\validate_final.py "build\从零开始的塔科夫生活_V1.2.2.exe"
if errorlevel 1 goto fail

echo.
echo Build complete: build\从零开始的塔科夫生活_V1.2.2.exe
pause
exit /b 0

:fail
echo.
echo Build failed. Check the error above.
pause
exit /b 1
