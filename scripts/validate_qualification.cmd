@echo off
setlocal
python "%~dp0validate_qualification.py" --root "%~dp0.." %*
exit /b %ERRORLEVEL%
