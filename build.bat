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

if not defined PYTHON set "PYTHON=py -3.11"

echo [1/5] compile ui_compact.py
%PYTHON% scripts\compile_ui.py
if errorlevel 1 goto fail

echo.
echo [2/5] generate sound_library.marshal
%PYTHON% scripts\patch_sound_library.py
if errorlevel 1 goto fail

echo.
echo [3/5] generate detector.marshal
%PYTHON% scripts\patch_detector.py
if errorlevel 1 goto fail

echo.
echo [4/5] repack PYZ
%PYTHON% scripts\repack_pyz.py "base\base_branded.exe" "build\从零开始的塔科夫生活_V1.exe"
if errorlevel 1 goto fail

echo.
echo [5/5] validate output
%PYTHON% scripts\validate_final.py "build\从零开始的塔科夫生活_V1.exe"
if errorlevel 1 goto fail

echo.
echo Build complete: build\从零开始的塔科夫生活_V1.exe
pause
exit /b 0

:fail
echo.
echo Build failed. Check the error above.
pause
exit /b 1
