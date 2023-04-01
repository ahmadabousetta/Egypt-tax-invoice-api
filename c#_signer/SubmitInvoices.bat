@REM We differentiate the calling directory from the app directory
@REM for cases when script is called from a scheduler.

set cwd=%cd%
set app_dir=%~dp0

cd /d "%app_dir%"

@REM use ~0,-1 to remove the trailing slash in folder path which results in escaping the " .
call publish\EInvoicingSigner.exe  "%app_dir:~0,-1%" 60906090 "Egypt Trust Sealing CA"

@REM uncomment the below line if you need to pause the cmd screen after it finishes to debug or read output.
@REM PAUSE
