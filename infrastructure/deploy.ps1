#Requires -Version 5.1
<#
.SYNOPSIS
    Despliega la infraestructura de DYGSOM Fraud Detection a Azure usando Bicep.

.DESCRIPTION
    Script de despliegue automatizado para Windows PowerShell.
    Valida prerequisitos, crea resource group, y despliega infraestructura.

.PARAMETER ResourceGroup
    Nombre del Resource Group (requerido)

.PARAMETER EnvName
    Ambiente: dev, qa, prod (default: dev)

.PARAMETER Location
    Azure region (default: eastus)

.PARAMETER BicepFile
    Archivo Bicep (default: dygsom-fraud-main.bicep)

.PARAMETER ParamsFile
    Archivo de parámetros (default: dygsom-fraud-main.parameters.json)

.PARAMETER ValidateOnly
    Solo validar, no desplegar

.EXAMPLE
    .\deploy.ps1 -ResourceGroup "rg-dygsom-fraud-dev" -EnvName "dev"

.EXAMPLE
    .\deploy.ps1 -ResourceGroup "rg-dygsom-fraud-prod" -EnvName "prod" -Location "westeurope"

.EXAMPLE
    .\deploy.ps1 -ResourceGroup "rg-dygsom-fraud-dev" -ValidateOnly
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "qa", "prod", "sandbox")]
    [string]$EnvName = "dev",

    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",

    [Parameter(Mandatory=$false)]
    [string]$BicepFile = "dygsom-fraud-main.bicep",

    [Parameter(Mandatory=$false)]
    [string]$ParamsFile = "dygsom-fraud-main.parameters.json",

    [Parameter(Mandatory=$false)]
    [switch]$ValidateOnly
)

#######################################################################
# Helper Functions
#######################################################################

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" "Green"
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" "Yellow"
}

function Write-ErrorCustom {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" "Red"
}

function Write-InfoCustom {
    param([string]$Message)
    Write-ColorOutput "ℹ $Message" "Cyan"
}

#######################################################################
# Validate Prerequisites
#######################################################################

Write-Header "Validando prerequisitos"

# Check if Azure CLI is installed
try {
    $null = Get-Command az -ErrorAction Stop
    Write-Success "Azure CLI encontrado"
} catch {
    Write-ErrorCustom "Azure CLI no está instalado. Instalar desde: https://learn.microsoft.com/cli/azure/install-azure-cli"
    exit 1
}

# Check if logged in
try {
    $accountInfo = az account show 2>&1 | ConvertFrom-Json
    Write-Success "Sesión de Azure autenticada"
    Write-InfoCustom "Suscripción activa: $($accountInfo.name) ($($accountInfo.id))"
} catch {
    Write-ErrorCustom "No estás autenticado. Ejecuta: az login"
    exit 1
}

# Check if Bicep file exists
if (-not (Test-Path $BicepFile)) {
    Write-ErrorCustom "Archivo Bicep no encontrado: $BicepFile"
    exit 1
}
Write-Success "Archivo Bicep encontrado: $BicepFile"

# Check if parameters file exists
if (-not (Test-Path $ParamsFile)) {
    Write-ErrorCustom "Archivo de parámetros no encontrado: $ParamsFile"
    exit 1
}
Write-Success "Archivo de parámetros encontrado: $ParamsFile"

#######################################################################
# Create Resource Group
#######################################################################

Write-Header "Configurando Resource Group"

$rgExists = az group exists --name $ResourceGroup | ConvertFrom-Json
if ($rgExists) {
    Write-Warning-Custom "Resource group '$ResourceGroup' ya existe"
    $existingRg = az group show --name $ResourceGroup | ConvertFrom-Json
    $existingLocation = $existingRg.location
    Write-InfoCustom "Ubicación actual: $existingLocation"

    if ($existingLocation -ne $Location) {
        Write-Warning-Custom "La ubicación solicitada ($Location) difiere de la existente ($existingLocation)"
        Write-Warning-Custom "Se usará la ubicación existente: $existingLocation"
        $Location = $existingLocation
    }
} else {
    Write-InfoCustom "Creando resource group '$ResourceGroup' en $Location..."
    az group create --name $ResourceGroup --location $Location --output none
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Resource group creado"
    } else {
        Write-ErrorCustom "Error al crear resource group"
        exit 1
    }
}

#######################################################################
# Validate Template
#######################################################################

Write-Header "Validando plantilla Bicep"

$validationResult = az deployment group validate `
    --resource-group $ResourceGroup `
    --template-file $BicepFile `
    --parameters "@$ParamsFile" `
    --parameters location=$Location envName=$EnvName `
    2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Validación exitosa"
} else {
    Write-ErrorCustom "Validación fallida:"
    Write-Host $validationResult
    exit 1
}

if ($ValidateOnly) {
    Write-Success "Validación completada. No se desplegó infraestructura (-ValidateOnly)"
    exit 0
}

#######################################################################
# Confirm Deployment
#######################################################################

Write-Header "Confirmación de Despliegue"

Write-Host "Estás a punto de desplegar:" -ForegroundColor Yellow
Write-Host "  Resource Group: " -NoNewline; Write-Host $ResourceGroup -ForegroundColor Green
Write-Host "  Ambiente:       " -NoNewline; Write-Host $EnvName -ForegroundColor Green
Write-Host "  Ubicación:      " -NoNewline; Write-Host $Location -ForegroundColor Green
Write-Host "  Bicep File:     " -NoNewline; Write-Host $BicepFile -ForegroundColor Green
Write-Host "  Parámetros:     " -NoNewline; Write-Host $ParamsFile -ForegroundColor Green
Write-Host ""

$confirmation = Read-Host "¿Continuar con el despliegue? (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Warning-Custom "Despliegue cancelado por el usuario"
    exit 0
}

#######################################################################
# Deploy Infrastructure
#######################################################################

Write-Header "Desplegando Infraestructura"

$deploymentName = "dygsom-fraud-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-InfoCustom "Nombre de despliegue: $deploymentName"
Write-InfoCustom "Tiempo estimado: 10-15 minutos..."
Write-Host ""

$deploymentOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file $BicepFile `
    --parameters "@$ParamsFile" `
    --parameters location=$Location envName=$EnvName `
    --name $deploymentName `
    --output json 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Despliegue completado exitosamente!"

    # Parse outputs
    $deployment = $deploymentOutput | ConvertFrom-Json
    $outputs = $deployment.properties.outputs

    #######################################################################
    # Display Outputs
    #######################################################################

    Write-Header "Recursos Desplegados"

    $dashboardUrl = if ($outputs.dashboardUrl) { $outputs.dashboardUrl.value } else { "N/A" }
    $apiUrl = if ($outputs.apiUrl) { $outputs.apiUrl.value } else { "N/A" }
    $postgresFqdn = if ($outputs.postgresFqdn) { $outputs.postgresFqdn.value } else { "N/A" }
    $redisHost = if ($outputs.redisHost) { $outputs.redisHost.value } else { "N/A" }
    $keyVaultUri = if ($outputs.keyVaultUri) { $outputs.keyVaultUri.value } else { "N/A" }

    Write-Host "Dashboard URL:    " -NoNewline; Write-Host $dashboardUrl -ForegroundColor Green
    Write-Host "API URL:          " -NoNewline; Write-Host $apiUrl -ForegroundColor Green
    Write-Host "PostgreSQL FQDN:  " -NoNewline; Write-Host $postgresFqdn -ForegroundColor Green
    Write-Host "Redis Host:       " -NoNewline; Write-Host $redisHost -ForegroundColor Green
    Write-Host "Key Vault URI:    " -NoNewline; Write-Host $keyVaultUri -ForegroundColor Green

    #######################################################################
    # Next Steps
    #######################################################################

    Write-Header "Próximos Pasos"

    Write-Host "1. Ejecutar migraciones de base de datos:"
    Write-Host "   az containerapp exec \" -ForegroundColor Cyan
    Write-Host "     --resource-group $ResourceGroup \" -ForegroundColor Cyan
    Write-Host "     --name ca-dygsom-fraud-api-$EnvName \" -ForegroundColor Cyan
    Write-Host "     --command `"/bin/sh -c 'prisma migrate deploy'`"" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "2. Verificar health de la API:"
    Write-Host "   curl $apiUrl/health" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "3. Ver logs en tiempo real:"
    Write-Host "   az containerapp logs show \" -ForegroundColor Cyan
    Write-Host "     --resource-group $ResourceGroup \" -ForegroundColor Cyan
    Write-Host "     --name ca-dygsom-fraud-api-$EnvName \" -ForegroundColor Cyan
    Write-Host "     --follow" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "4. Acceder al dashboard:"
    Write-Host "   $dashboardUrl" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "5. Ver documentación de API:"
    Write-Host "   $apiUrl/docs" -ForegroundColor Cyan
    Write-Host ""

    # Save outputs to file
    $outputsFile = "deployment-outputs-$EnvName.txt"
    $outputContent = @"
DYGSOM Fraud Detection - Deployment Outputs
Environment: $EnvName
Deployed: $(Get-Date)
Deployment Name: $deploymentName

Dashboard URL:    $dashboardUrl
API URL:          $apiUrl
PostgreSQL FQDN:  $postgresFqdn
Redis Host:       $redisHost
Key Vault URI:    $keyVaultUri
"@

    $outputContent | Out-File -FilePath $outputsFile -Encoding utf8
    Write-Success "Outputs guardados en: $outputsFile"

} else {
    Write-ErrorCustom "Despliegue fallido. Revisa el output arriba para detalles."
    Write-Host $deploymentOutput
    exit 1
}

Write-Header "Despliegue Finalizado"
Write-Success "¡Infraestructura desplegada exitosamente!"
