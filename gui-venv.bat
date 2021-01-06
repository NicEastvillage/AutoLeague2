@ECHO OFF
cmd /k "%LocalAppData%\RLBotGUIX\venv\Scripts\activate.bat & python -m pip install -r requirements.txt & cd autoleague"
