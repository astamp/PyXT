@ECHO OFF

nasm temp.asm -f bin -o temp.bin
IF ERRORLEVEL 1 GOTO END

ndisasm temp.bin

:END
