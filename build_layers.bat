@echo off
setlocal enabledelayedexpansion

:: Remove existing virtual environment if it exists
if exist .venv (
    echo Removing existing virtual environment...
    rmdir /s /q .venv
)

:: Create a new virtual environment
echo Creating new virtual environment...
py -m venv .venv

:: Activate the virtual environment
call .venv\Scripts\activate

:: Install main dependencies
echo Installing Python dependencies from requirements.txt...
py -m pip install -r requirements.txt

:: Rebuild action lambda libraries
echo Cleaning and rebuilding action lambda libraries...
if exist ..\lambda_layer\action_lambda\lib (
    rmdir /s /q ..\lambda_layer\action_lambda\lib
)
mkdir ..\lambda_layer\action_lambda\lib\python
py -m pip install -r .\action_lambda\requirements.txt -t ..\lambda_layer\action_lambda\lib\python

:: Copy action_lambda package to the layer
echo Copying action_lambda package to Lambda layer...
xcopy /E /I /Y ..\action_lambda ..\lambda_layer\action_lambda\lib\python\action_lambda

:: Create zip file for the layer
echo Creating zip file for Lambda layer...
cd ..\lambda_layer\action_lambda\lib\python
echo Current directory: %CD%
echo Creating zip file...
powershell -Command "Compress-Archive -Path * -DestinationPath ..\..\..\python.zip -Force"
if exist ..\..\..\python.zip (
    echo Successfully created zip file at: ..\..\..\python.zip
) else (
    echo ERROR: Failed to create zip file!
)
cd ..\..\..\..\..

:: Verify the installation
echo Verifying package installation...
dir ..\lambda_layer\action_lambda\lib\python\pymysql
dir ..\lambda_layer\action_lambda\lib\python\DBUtils
dir ..\lambda_layer\action_lambda\lib\python\mysql

echo.
echo All tasks completed successfully!
echo Layer zip file should be at: ..\lambda_layer\action_lambda\python.zip

endlocal 