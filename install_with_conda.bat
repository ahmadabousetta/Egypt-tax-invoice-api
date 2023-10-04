@REM Use this line to activate the correct environment with the correct openssl version
call conda create -n taxes python=3.11 openssl=1
call conda activate taxes
python -m pip install -r requirements.txt
call conda deactivate
@REM Press any key to continue message
pause
