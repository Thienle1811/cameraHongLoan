@echo off
REM Script build .exe cho Windows
REM Chạy script này để đóng gói ứng dụng thành file .exe

echo ========================================
echo Building Parking Control System
echo ========================================

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Kiểm tra xem đã cài PyInstaller chưa
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Build với spec file
echo Building executable...
pyinstaller build_exe.spec --clean

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Copy config.json và sounds/ vào dist nếu chưa có
if not exist "dist\config.json" (
    if exist "config.json" (
        echo Copying config.json...
        copy "config.json" "dist\" >nul
    )
)

if not exist "dist\sounds" (
    if exist "sounds" (
        echo Copying sounds folder...
        xcopy "sounds" "dist\sounds\" /E /I /Y >nul
    )
)

echo.
echo ========================================
echo Build completed successfully!
echo Executable location: dist\ParkingControlSystem.exe
echo ========================================
echo.
echo Files in dist folder:
echo   - ParkingControlSystem.exe
if exist "dist\config.json" echo   - config.json
if exist "dist\sounds" echo   - sounds\ (with audio files)
echo.
echo Note: If config.json or sounds/ are missing, copy them manually
echo.

pause

