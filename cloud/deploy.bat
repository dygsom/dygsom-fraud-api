@echo off
REM DYGSOM Fraud API - Azure Deployment Script (Windows)
REM This script deploys the application to Azure using Azure Developer CLI (azd)

echo 🚀 DYGSOM Fraud API - Azure Deployment
echo ========================================

REM Check if we're in the cloud directory
if not exist "azure.yaml" (
    echo ❌ Error: azure.yaml not found. Please run this script from the cloud directory.
    exit /b 1
)

REM Check required tools
echo 🔍 Checking required tools...

az version >nul 2>&1
if errorlevel 1 (
    echo ❌ Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
    exit /b 1
)

azd version >nul 2>&1
if errorlevel 1 (
    echo ❌ Azure Developer CLI not found. Please install: https://docs.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd
    exit /b 1
)

docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop
    exit /b 1
)

echo ✅ All required tools are installed

REM Check Azure login
echo 🔐 Checking Azure authentication...
az account show >nul 2>&1
if errorlevel 1 (
    echo 🔑 Please login to Azure...
    az login
)

REM Initialize azd if not already done
if not exist ".azure\config.json" (
    echo 🎯 Initializing Azure Developer CLI...
    azd init --template minimal
)

REM Set up environment if .env doesn't exist
if not exist ".env" (
    echo ⚙️  Setting up environment configuration...
    copy .env.template .env
    echo 📝 Please edit .env file with your configuration:
    echo    - AZURE_ENV_NAME: Choose environment name ^(e.g., dygsom-dev^)
    echo    - AZURE_LOCATION: Choose Azure region ^(e.g., East US^)
    echo    - AZURE_SUBSCRIPTION_ID: Your Azure subscription ID
    echo.
    echo Then run this script again.
    exit /b 0
)

REM Load environment variables (basic check)
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="AZURE_ENV_NAME" set AZURE_ENV_NAME=%%b
    if "%%a"=="AZURE_LOCATION" set AZURE_LOCATION=%%b
)

REM Remove quotes from environment variables
set AZURE_ENV_NAME=%AZURE_ENV_NAME:"=%
set AZURE_LOCATION=%AZURE_LOCATION:"=%

if "%AZURE_ENV_NAME%"=="" (
    echo ❌ Error: Please set AZURE_ENV_NAME in .env file
    exit /b 1
)

if "%AZURE_LOCATION%"=="" (
    echo ❌ Error: Please set AZURE_LOCATION in .env file
    exit /b 1
)

echo 🏗️  Deploying to Azure...
echo    Environment: %AZURE_ENV_NAME%
echo    Location: %AZURE_LOCATION%

REM Build and deploy
azd up

echo.
echo 🎉 Deployment completed successfully!
echo.
echo 📊 Next steps:
echo 1. Check deployment status: azd show
echo 2. View logs: azd logs
echo 3. Monitor costs: Check Azure Cost Management
echo 4. Set up monitoring alerts in Azure portal
echo.
echo 🔗 Useful commands:
echo    azd show     - Show deployment details
echo    azd logs     - View application logs
echo    azd down     - Delete all resources
echo    azd deploy   - Deploy code changes only