@echo off
python "%~dp0selftest_qualification_validator.py"
exit /b %ERRORLEVEL%
