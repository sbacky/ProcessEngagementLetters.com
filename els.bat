@echo off
cd /d "%~dp0"

echo Searching for Google Chrome...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
) else (
    echo Google Chrome not found. Falling back to the default browser.
    set CHROME_PATH=
)

echo Checking for virtual environment...
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment found.
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Setting environment variables...
set HOST=localhost
set PORT=5000
set DEBUG=False

echo Pulling latest version from GitHub...
git pull

echo Installing requirements...
pip install -r .\requirements.txt

echo Running main.py...
python main.py --host %HOST% --port %PORT% --debug %DEBUG%

pause