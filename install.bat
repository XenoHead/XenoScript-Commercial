@echo off
echo ==========================================
echo Installing XenoScript 1.0...
echo ==========================================
echo.

:: 1. Create the Directory
echo Creating installation folder at C:\XenoScript...
if not exist "C:\XenoScript" mkdir "C:\XenoScript"

:: 2. Copy the Executable
echo Copying XenoScript.exe to installation folder...
if exist "%~dp0dist\XenoScript.exe" (
    copy /Y "%~dp0dist\XenoScript.exe" "C:\XenoScript\XenoScript.exe"
) else if exist "%~dp0XenoScript.exe" (
    copy /Y "%~dp0XenoScript.exe" "C:\XenoScript\XenoScript.exe"
) else (
    echo ERROR: Could not find XenoScript.exe! Please make sure it is in the same folder as this installer.
    pause
    exit /b
)

:: 2b. Copy the Sample Project
echo Copying SampleProject.xsp to installation folder...
if exist "%~dp0SampleProject.xsp" (
    copy /Y "%~dp0SampleProject.xsp" "C:\XenoScript\SampleProject.xsp"
)

:: 3. Set the Environment Variable (Persistent for User)
echo Setting up the AI Assistant API Key...
:: Removed hardcoded leaked key. The user will set this inside the app from the Customize menu.

:: 4. Create Desktop Shortcut using VBScript
echo Creating Desktop shortcut...
set VBS_SCRIPT="%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %VBS_SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\XenoScript.lnk" >> %VBS_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %VBS_SCRIPT%
echo oLink.TargetPath = "C:\XenoScript\XenoScript.exe" >> %VBS_SCRIPT%
echo oLink.WorkingDirectory = "C:\XenoScript" >> %VBS_SCRIPT%
echo oLink.Description = "XenoScript Pro Screenplay Editor" >> %VBS_SCRIPT%
echo oLink.IconLocation = "C:\XenoScript\XenoScript.exe, 0" >> %VBS_SCRIPT%
echo oLink.Save >> %VBS_SCRIPT%

cscript /nologo %VBS_SCRIPT%
del %VBS_SCRIPT%

:: 5. Associate File Extensions (.xsp and .ksp)
echo Associating project files with XenoScript...
:: Step 1: Define the file type and link it to the executable program
ftype XenoScriptProject="C:\XenoScript\XenoScript.exe" "%%1"

:: Step 2: Associate the file extensions with that newly defined file type
assoc .xsp=XenoScriptProject
assoc .ksp=XenoScriptProject

echo.
echo ==========================================
echo Installation Complete!
echo XenoScript has been installed to C:\XenoScript
echo and a shortcut was placed on the Desktop.
echo ==========================================
pause