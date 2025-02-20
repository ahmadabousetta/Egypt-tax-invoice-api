@REM We differentiate the calling directory from the app directory
@REM for cases when script is called from a scheduler.

set "cwd=%cd%"
set "app_dir=%~dp0"

cd /d "%app_dir%"

call conda activate taxes
python tax_script.py
call conda deactivate

@REM cd /d "%cwd%"
PAUSE

