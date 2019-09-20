start RKeeperInfo.exe
echo off
cls
REM WinCash update and start
SET PRELOADPATH=.\PRELOAD
if /%1 == / goto defini
SET CASHINIPATH=%1
goto now_run

:defini
SET CASHINIPATH=.\wincash.ini

:now_run
cls
echo y|preload.exe %CASHINIPATH%
if %ERRORLEVEL%==0 goto continue
if %ERRORLEVEL%==4002 goto 4002
if %ERRORLEVEL%==4003 goto 4003
if %ERRORLEVEL%==4004 goto 4004
if %ERRORLEVEL%==4006 goto 4006
if %ERRORLEVEL%==4010 goto 4010
if %ERRORLEVEL%==4030 goto 4030
if %ERRORLEVEL%==4031 goto 4031
cls
echo Unknown error
echo �������⭠� �訡��
ping 127.0.0.1 -n 10 > nul
goto now_run

:4002
cls
echo Can not create directory: "path".
echo ���������� ᮧ���� ��⠫��: "path".
echo ��१���� �१ 10 ᥪ㭤...
ping 127.0.0.1 -n 10 > nul
goto now_run

:4003
cls
echo Exception during receiving modules.
echo �訡�� �� �६� ����祭�� ���㫥�.
echo ��१���� �१ 10 ᥪ㭤...
ping 127.0.0.1 -n 10 > nul
goto now_run

:4004
cls
echo This station is not defined (Net name).
echo ��� �⠭樨 � ⠪�� �⥢� ������ �� �ࢥ�.
echo ��१���� �१ 10 ᥪ㭤...
ping 127.0.0.1 -n 10 > nul
goto now_run

:4006
cls
echo Exception during modules description receiving.
echo �訡�� �� ����祭�� ᯨ᪠ ���㫥�.
echo ��१���� �१ 10 ᥪ㭤...
ping 127.0.0.1 -n 10 > nul
goto now_run

:4010
cls
echo Can not read ini file .\WINCASH.INI: Win error.
echo �� ������ WINCASH.INI
echo ��१���� �१ 10 ᥪ㭤...
ping 127.0.0.1 -n 10 > nul
goto now_run

:4030
cls
echo Can not initialize network. May be process with same "Station" name exists.
echo ���ࠢ��쭮 ����஥�� ��� ��� ������� ����� � ⥬ �� ������ �⠭樨.
echo ��१���� �१ 10 ᥪ㭤...
ping 127.0.0.1 -n 10 > nul
goto now_run

:4031
cls
echo Server not found.
echo ��ࢥ� �� ������.
echo ��१���� �१ 10 ᥪ㭤...
ping 127.0.0.1 -n 10 > nul
goto now_run

:nork7copy
echo rk7copy.exe not found
pause

:continue
if not EXIST rk7copy.exe goto nork7copy
for %%c in (%PRELOADPATH%\*.dll) do del /F %%~nc.bak
for %%c in (%PRELOADPATH%\*.dll) do ren %%~nc.dll *.bak

rk7copy %PRELOADPATH% .\ /S /C
rmdir %PRELOADPATH% /S /Q

start doscash.exe %CASHINIPATH%
