@REM We differentiate the calling directory from the app directory
@REM for cases when script is called from a scheduler.

set cwd=%cd%
set app_dir=%~dp0

cd /d "%app_dir%"


call publish\EInvoicingSigner.exe  %app_dir% 60906090 "Egypt Trust Sealing CA"
PAUSE