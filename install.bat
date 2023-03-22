
@REM We use py assuming a windows environment, if you are on linux or mac, use python instead of py
py -m venv .venv
call .venv\Scripts\activate.bat
py -m pip install -r requirements.txt

@REM Press any key to continue message
pause