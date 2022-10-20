@ECHO OFF

nasm temp.asm -f bin -o temp.bin
IF ERRORLEVEL 1 GOTO END

echo ========================================================================
ndisasm temp.bin
echo ========================================================================
python -c "import binascii; raw = open('temp.bin', 'rb').read(); data = binascii.hexlify(raw).decode('ascii').upper(); print(' '.join([data[x : x + 2] for x in range(0, len(data), 2)]))"
echo ========================================================================

:END
