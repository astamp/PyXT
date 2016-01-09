@ECHO OFF
SETLOCAL

SET PATTERN=%1
SET ARGS=

:LOOP
SHIFT
IF "%1"=="" GOTO DONE
SET ARGS=%ARGS% %1
GOTO LOOP
:DONE

ECHO Deleting previous run...
DEL /S /Q htmlcov >NUL
DEL /S /Q .coverage >NUL

ECHO Running unit tests with coverage...
python -m coverage run -m unittest discover -p test_%PATTERN%* %ARGS%

ECHO Generating HTML report...
python -m coverage html

ECHO DONE!
ENDLOCAL
