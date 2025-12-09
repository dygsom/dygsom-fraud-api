#Requires -Version 5.1
<#
.SYNOPSIS
    Valida si los contenedores en Azure Container Apps están usando las últimas versiones de las imágenes.

.DESCRIPTION
    Este script verifica el estado actual de los Container Apps desplegados y compara
    con las imágenes configuradas en la plantilla Bicep y los últimos commits en GitHub.

.PARAMETER ResourceGroup
    Nombre del Resource Group donde están desplegados los Container Apps (default: rg-dygsom-fraud-mvp)

.PARAMETER UpdateImages
    Si se especifica, actualiza los Container Apps con las últimas imágenes

.EXAMPLE
    .\check-container-versions.ps1

.EXAMPLE
    .\check-container-versions.ps1 -UpdateImages
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "rg-dygsom-fraud-mvp",

    [Parameter(Mandatory=$false)]
    [switch]$UpdateImages
)

Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "  VALIDACION DE VERSIONES DE IMAGENES DE CONTENEDORES" -ForegroundColor Blue
Write-Host "================================================================================" -ForegroundColor Blue

# Verificar si Azure CLI está disponible
try {
    az --version | Out-Null
    Write-Host "Azure CLI: OK" -ForegroundColor Green
} catch {
    Write-Host "Error: Azure CLI no está instalado o no está en PATH" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Blue

# Obtener información de los Container Apps
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "  INFORMACION ACTUAL DE CONTAINER APPS" -ForegroundColor Blue
Write-Host "================================================================================" -ForegroundColor Blue

$apiInfo = az containerapp show --name ca-api-dev --resource-group $ResourceGroup --query "{Name:name, Image:properties.template.containers[0].image, LastModified:systemData.lastModifiedAt, ActiveRevision:properties.latestRevisionName}" --output json | ConvertFrom-Json

$dashboardInfo = az containerapp show --name ca-dashboard-dev --resource-group $ResourceGroup --query "{Name:name, Image:properties.template.containers[0].image, LastModified:systemData.lastModifiedAt, ActiveRevision:properties.latestRevisionName}" --output json | ConvertFrom-Json

if (-not $apiInfo -or -not $dashboardInfo) {
    Write-Host "Error: No se pudo obtener información de los Container Apps" -ForegroundColor Red
    exit 1
}

Write-Host "API Container App:" -ForegroundColor Green
Write-Host "  Imagen actual: $($apiInfo.Image)"
Write-Host "  Ultima modificacion: $($apiInfo.LastModified)"
Write-Host "  Revision activa: $($apiInfo.ActiveRevision)"

Write-Host ""
Write-Host "Dashboard Container App:" -ForegroundColor Green
Write-Host "  Imagen actual: $($dashboardInfo.Image)"
Write-Host "  Ultima modificacion: $($dashboardInfo.LastModified)"
Write-Host "  Revision activa: $($dashboardInfo.ActiveRevision)"

# Obtener información de Git
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "  INFORMACION DE REPOSITORIOS GIT" -ForegroundColor Blue
Write-Host "================================================================================" -ForegroundColor Blue

$currentDir = Get-Location
$apiRepoPath = $currentDir.Path
$parentDir = Split-Path $currentDir.Path -Parent
$dashboardRepoPath = Join-Path $parentDir "dygsom-fraud-dashboard"

# API Repository
try {
    Set-Location $apiRepoPath
    $apiCommitHash = git rev-parse HEAD
    $apiCommitDate = git log -1 --format=%cd --date=iso
    $apiCommitMessage = git log -1 --format=%s
    
    Write-Host "API Repository:" -ForegroundColor Green
    Write-Host "  Ultimo commit: $($apiCommitHash.Substring(0, 7))"
    Write-Host "  Fecha: $apiCommitDate"
    Write-Host "  Mensaje: $apiCommitMessage"
} catch {
    Write-Host "Warning: No se pudo obtener información de Git para API" -ForegroundColor Yellow
}

Write-Host ""

# Dashboard Repository
if (Test-Path $dashboardRepoPath) {
    try {
        Set-Location $dashboardRepoPath
        $dashboardCommitHash = git rev-parse HEAD
        $dashboardCommitDate = git log -1 --format=%cd --date=iso
        $dashboardCommitMessage = git log -1 --format=%s
        
        Write-Host "Dashboard Repository:" -ForegroundColor Green
        Write-Host "  Ultimo commit: $($dashboardCommitHash.Substring(0, 7))"
        Write-Host "  Fecha: $dashboardCommitDate"
        Write-Host "  Mensaje: $dashboardCommitMessage"
    } catch {
        Write-Host "Warning: No se pudo obtener información de Git para Dashboard" -ForegroundColor Yellow
    }
} else {
    Write-Host "Warning: No se encontró el repositorio del Dashboard en $dashboardRepoPath" -ForegroundColor Yellow
}

# Volver al directorio original
Set-Location $currentDir

# Análisis de versiones
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "  ANALISIS DE VERSIONES" -ForegroundColor Blue
Write-Host "================================================================================" -ForegroundColor Blue

$apiUsingMain = $apiInfo.Image.EndsWith(":main")
$dashboardUsingMain = $dashboardInfo.Image.EndsWith(":main")

Write-Host "API:" -ForegroundColor Blue
Write-Host "  Imagen actual: $($apiInfo.Image)"
if ($apiUsingMain) {
    Write-Host "  Estado: ACTUALIZADO (usando tag 'main')" -ForegroundColor Green
} else {
    Write-Host "  Estado: NO ACTUALIZADO (no usando tag 'main')" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Dashboard:" -ForegroundColor Blue
Write-Host "  Imagen actual: $($dashboardInfo.Image)"
if ($dashboardUsingMain) {
    Write-Host "  Estado: ACTUALIZADO (usando tag 'main')" -ForegroundColor Green
} else {
    Write-Host "  Estado: NO ACTUALIZADO (no usando tag 'main')" -ForegroundColor Yellow
}

# Verificar si hay actualizaciones disponibles
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "  VERIFICACION DE ACTUALIZACIONES" -ForegroundColor Blue
Write-Host "================================================================================" -ForegroundColor Blue

$needsUpdate = $false

# Comparar fechas si tenemos la información de Git
if ($apiCommitDate -and $apiInfo.LastModified) {
    try {
        $apiDeployDate = [DateTime]::Parse($apiInfo.LastModified)
        $apiCommitDateParsed = [DateTime]::Parse($apiCommitDate)
        
        if ($apiCommitDateParsed -gt $apiDeployDate) {
            Write-Host "API: Hay commits mas recientes que el ultimo despliegue" -ForegroundColor Yellow
            Write-Host "   Ultimo commit: $apiCommitDate"
            Write-Host "   Ultimo despliegue: $($apiInfo.LastModified)"
            $needsUpdate = $true
        } else {
            Write-Host "API: El despliegue esta sincronizado con los commits" -ForegroundColor Green
        }
    } catch {
        Write-Host "API: No se pudo comparar fechas de commit vs despliegue" -ForegroundColor Yellow
    }
}

if ($dashboardCommitDate -and $dashboardInfo.LastModified) {
    try {
        $dashboardDeployDate = [DateTime]::Parse($dashboardInfo.LastModified)
        $dashboardCommitDateParsed = [DateTime]::Parse($dashboardCommitDate)
        
        if ($dashboardCommitDateParsed -gt $dashboardDeployDate) {
            Write-Host "Dashboard: Hay commits mas recientes que el ultimo despliegue" -ForegroundColor Yellow
            Write-Host "   Ultimo commit: $dashboardCommitDate"
            Write-Host "   Ultimo despliegue: $($dashboardInfo.LastModified)"
            $needsUpdate = $true
        } else {
            Write-Host "Dashboard: El despliegue esta sincronizado con los commits" -ForegroundColor Green
        }
    } catch {
        Write-Host "Dashboard: No se pudo comparar fechas de commit vs despliegue" -ForegroundColor Yellow
    }
}

# Actualizar si se solicita
if ($UpdateImages -and ($needsUpdate -or -not $apiUsingMain -or -not $dashboardUsingMain)) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Blue
    Write-Host "  ACTUALIZANDO IMAGENES" -ForegroundColor Blue
    Write-Host "================================================================================" -ForegroundColor Blue
    
    if ($apiUsingMain) {
        Write-Host "Actualizando API con la ultima version de main..." -ForegroundColor Yellow
        try {
            az containerapp update --name ca-api-dev --resource-group $ResourceGroup --image "ghcr.io/dygsom/dygsom-fraud-api:main" --output none
            Write-Host "API actualizado exitosamente" -ForegroundColor Green
        } catch {
            Write-Host "Error actualizando API" -ForegroundColor Red
        }
    }
    
    if ($dashboardUsingMain) {
        Write-Host "Actualizando Dashboard con la ultima version de main..." -ForegroundColor Yellow
        try {
            az containerapp update --name ca-dashboard-dev --resource-group $ResourceGroup --image "ghcr.io/dygsom/dygsom-fraud-dashboard:main" --output none
            Write-Host "Dashboard actualizado exitosamente" -ForegroundColor Green
        } catch {
            Write-Host "Error actualizando Dashboard" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "Nota: Las actualizaciones pueden tomar unos minutos en surtir efecto." -ForegroundColor Yellow
} elseif ($UpdateImages) {
    Write-Host "No se requieren actualizaciones" -ForegroundColor Green
} elseif ($needsUpdate -or -not $apiUsingMain -or -not $dashboardUsingMain) {
    Write-Host ""
    Write-Host "Para actualizar las imagenes, ejecuta:" -ForegroundColor Yellow
    Write-Host "   .\check-container-versions.ps1 -UpdateImages" -ForegroundColor Yellow
}

# Resumen final
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "  RESUMEN FINAL" -ForegroundColor Blue
Write-Host "================================================================================" -ForegroundColor Blue

if ($needsUpdate -or -not $apiUsingMain -or -not $dashboardUsingMain) {
    Write-Host "ACCION REQUERIDA: Revisar y actualizar contenedores" -ForegroundColor Yellow
} else {
    Write-Host "ESTADO OPTIMO: Todos los contenedores estan actualizados" -ForegroundColor Green
}

Write-Host ""
Write-Host "URLs de acceso:" -ForegroundColor Blue
Write-Host "  API: Verificar con az containerapp show --name ca-api-dev --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn" -ForegroundColor Blue
Write-Host "  Dashboard: Verificar con az containerapp show --name ca-dashboard-dev --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn" -ForegroundColor Blue