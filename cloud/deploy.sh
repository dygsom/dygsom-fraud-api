#!/bin/bash

# DYGSOM Fraud API - Azure Deployment Script
# This script deploys the application to Azure using Azure Developer CLI (azd)

set -e

echo "🚀 DYGSOM Fraud API - Azure Deployment"
echo "========================================"

# Check if we're in the cloud directory
if [ ! -f "azure.yaml" ]; then
    echo "❌ Error: azure.yaml not found. Please run this script from the cloud directory."
    exit 1
fi

# Check required tools
echo "🔍 Checking required tools..."

if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

if ! command -v azd &> /dev/null; then
    echo "❌ Azure Developer CLI not found. Please install: https://docs.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop"
    exit 1
fi

echo "✅ All required tools are installed"

# Check Azure login
echo "🔐 Checking Azure authentication..."
if ! az account show &> /dev/null; then
    echo "🔑 Please login to Azure..."
    az login
fi

# Initialize azd if not already done
if [ ! -f ".azure/config.json" ]; then
    echo "🎯 Initializing Azure Developer CLI..."
    azd init --template minimal
fi

# Set up environment if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up environment configuration..."
    cp .env.template .env
    echo "📝 Please edit .env file with your configuration:"
    echo "   - AZURE_ENV_NAME: Choose environment name (e.g., dygsom-dev)"
    echo "   - AZURE_LOCATION: Choose Azure region (e.g., East US)"
    echo "   - AZURE_SUBSCRIPTION_ID: Your Azure subscription ID"
    echo ""
    echo "Then run this script again."
    exit 0
fi

# Load environment variables
source .env

# Validate required environment variables
if [ -z "$AZURE_ENV_NAME" ] || [ -z "$AZURE_LOCATION" ]; then
    echo "❌ Error: Please set AZURE_ENV_NAME and AZURE_LOCATION in .env file"
    exit 1
fi

echo "🏗️  Deploying to Azure..."
echo "   Environment: $AZURE_ENV_NAME"
echo "   Location: $AZURE_LOCATION"

# Build and deploy
azd up

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Next steps:"
echo "1. Check deployment status: azd show"
echo "2. View logs: azd logs"
echo "3. Monitor costs: Check Azure Cost Management"
echo "4. Set up monitoring alerts in Azure portal"
echo ""
echo "🔗 Useful commands:"
echo "   azd show     - Show deployment details"
echo "   azd logs     - View application logs"
echo "   azd down     - Delete all resources"
echo "   azd deploy   - Deploy code changes only"