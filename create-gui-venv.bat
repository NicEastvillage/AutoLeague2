@ECHO OFF
echo Creating virtual environment using RLBotGUI's Python ...
cd %~dp0
cmd /c "%LocalAppData%\RLBotGUIX\Python311\python.exe -m venv venv & venv\\Scripts\\pip.exe install -r requirements.txt"
pause
