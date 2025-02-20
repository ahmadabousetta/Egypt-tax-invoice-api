set "app_dir=%~dp0"

@REM Replace 60906090 with your token PIN and "Egypt Trust Sealing CA" with your certificate issuer.
call "%app_dir%\publish\EInvoicingSigner.exe"  "%app_dir" 60906090 "Egypt Trust Sealing CA"

@REM uncomment the below line if you need to pause the cmd screen after it finishes to debug or read output.
@REM PAUSE
