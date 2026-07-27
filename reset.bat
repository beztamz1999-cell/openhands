@echo off
echo ========================================
echo  REI Checker - Reset & Update Script
echo ========================================
echo.

REM Xoa cache Python
echo [1/4] Xoa Python cache...
if exist __pycache__ rmdir /s /q __pycache__
if exist checkers\__pycache__ rmdir /s /q checkers\__pycache__
if exist gui\__pycache__ rmdir /s /q gui\__pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
echo    Da xoa cache xong!

REM Pull code moi
echo.
echo [2/4] Pull code moi tu GitHub...
git pull origin main
if errorlevel 1 (
    echo.
    echo Loi git! Thu chay thu cong cua Git Bash.
    pause
    exit /b 1
)
echo    Pull thanh cong!

REM Kiem tra file
echo.
echo [3/4] Kiem tra file can thiet...
if not exist ".env" (
    echo    Tao file .env moi...
    echo. > .env
    echo VUI LONG NHAP TOKEN VAO FILE .env!
    notepad .env
)
echo    OK!

REM Chay app
echo.
echo [4/4] Khoi dong REI Checker...
echo.
python main.py

pause
