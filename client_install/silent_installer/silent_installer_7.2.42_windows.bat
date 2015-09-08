@ECHO OFF
SETLOCAL
SET rst=no
GOTO parse

:usage
ECHO Usage: [/?] [/r]
ECHO.
ECHO    /h Display this text.
ECHO    /r Restart once installation is complete. Default: no.
GOTO end

:: PARSE ANY CMDLINE ARGS
:parse
IF [%1]==[] GOTO endparse
IF [%1]==[/?] GOTO usage && exit \b 0
IF [%1]==[/r] SET rst=yes && ECHO Will restart when complete.
SHIFT
GOTO parse
:endparse

:: BOINC CLIENT INSTALLATION
:: ADD PROJECT SPECIFIC INFORMATION HERE
SET projurl=""
SET projauth=""
SET acctfile=""
SET datadir="%PROGRAMDATA%\BOINC\"

ECHO Silent install beginning...
boinc_7.2.42_windows_x86_64.exe /S /v"/qn ENABLEPROTECTEDAPPLICATIONEXECUTION3=1 ENABLESCREENSAVER=0 ENABLEUSEBYALLUSERS=0 ENABLESTARTMENUITEMS=0 LAUNCHPROGRAM=0 RebootYesNo=No PROJINIT_URL=%projurl% PROJINT_AUTH=%projauth%"

:: BOINC CLIENT CONFIGURATION

ECHO Copying configuration files...
COPY cc_config.xml %datadir%
COPY %acctfile% %datadir%
::COPY global_prefs_override.xml %datadir%
COPY remote_hosts.cfg %datadir%
DEL "%datadir%global_prefs_override.xml"

:: DISABLE BOINCMGR STARTUP
set boinckey="HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

ECHO Disabling auto-startup and altering registry...
REG QUERY %boinckey% /v boincmgr 1>nul 2>&1 && REG DELETE %boinckey% /v boincmgr /f
REG QUERY %boinckey% /v boinctray 1>nul 2>&1 && REG DELETE %boinckey% /v boinctray /f
IF EXIST "%USERPROFILE%\Start Menu\Programs\BOINC" RMDIR /S /Q "%USERPROFILE$\Start Menu\Programs\BOINC"
IF EXIST "%APPDATA%\Microsoft\Windows\Start Menu\Programs\BOINC" RMDIR \S \Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\BOINC"

:: THIS IS/WAS NEEDED FOR OLD VERSION OF THE WRAPPER TO FUNCTION PROPERLY
:: PRE 26011 versions
ECHO Upgrading boinc accounts to administrator...
net localgroup administrators "boinc_project" /add 2> silent_install.log
net localgroup administrators "boinc_master" /add 2> silent_install.log

ECHO Installation and configuration complete.
IF %rst%==yes (
    ECHO Restarting...
    shutdown /r
) ELSE (
    ECHO Exiting...
)

:end
ENDLOCAL
