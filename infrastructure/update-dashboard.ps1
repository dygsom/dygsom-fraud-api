#Requires -Version 5.1
<#
.SYNOPSIS
    Valida y actualiza el dashboard con la última versión del código

.DESCRIPTION
    Compara la fecha del último despliegue con los commits más recientes y actualiza si es necesario

.PARAMETER ForceUpdate
    Fuerza la actualización del dashboard incluso si parece estar actualizado
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$ForceUpdate
)

$ResourceGroup = "rg-dygsom-fraud-mvp"
$DashboardApp = "ca-dashboard-dev"

Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "  VALIDACION Y ACTUALIZACION DEL DASHBOARD" -ForegroundColor Blue
Write-Host "================================================================================" -ForegroundColor Blue

# Obtener información actual del dashboard
Write-Host "Obteniendo información actual del Container App..." -ForegroundColor Yellow

$dashboardInfo = az containerapp show --name $DashboardApp --resource-group $ResourceGroup --query "{Name:name, Image:properties.template.containers[0].image, LastModified:systemData.lastModifiedAt, ActiveRevision:properties.latestRevisionName}" --output json | ConvertFrom-Json

Write-Host "Dashboard Container App:" -ForegroundColor Green
Write-Host "  Nombre: $($dashboardInfo.Name)"
Write-Host "  Imagen: $($dashboardInfo.Image)"
Write-Host "  Ultima modificacion: $($dashboardInfo.LastModified)"
Write-Host "  Revision activa: $($dashboardInfo.ActiveRevision)"

# Obtener información del repositorio Git
Write-Host ""
Write-Host "Obteniendo información del repositorio..." -ForegroundColor Yellow

$currentDir = Get-Location
$dashboardRepoPath = "D:\code\dygsom\dygsom-fraud-dashboard"

try {
    Set-Location $dashboardRepoPath
    $lastCommitInfo = git log -1 --format="%H|%cd|%s" --date=iso
    $commitParts = $lastCommitInfo -split '\|'
    
    Write-Host "Repositorio Dashboard:" -ForegroundColor Green
    Write-Host "  Ultimo commit: $($commitParts[0].Substring(0, 7))"
    Write-Host "  Fecha commit: $($commitParts[1])"
    Write-Host "  Mensaje: $($commitParts[2])"
    
    # Comparar fechas
    $deployDate = [DateTime]::Parse($dashboardInfo.LastModified)
    $commitDate = [DateTime]::Parse($commitParts[1])
    
    Write-Host ""
    Write-Host "ANALISIS:" -ForegroundColor Cyan
    Write-Host "  Fecha despliegue: $($deployDate.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "  Fecha ultimo commit: $($commitDate.ToString('yyyy-MM-dd HH:mm:ss'))"
    
    $needsUpdate = $commitDate -gt $deployDate
    
    if ($needsUpdate) {
        Write-Host "  RESULTADO: REQUIERE ACTUALIZACION" -ForegroundColor Yellow
        Write-Host "  Diferencia: $([Math]::Round(($commitDate - $deployDate).TotalMinutes, 2)) minutos mas reciente"
    } else {
        Write-Host "  RESULTADO: ESTA ACTUALIZADO" -ForegroundColor Green
    }
    
    if ($ForceUpdate -or $needsUpdate) {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Blue
        Write-Host "  ACTUALIZANDO DASHBOARD" -ForegroundColor Blue
        Write-Host "================================================================================" -ForegroundColor Blue
        
        # Forzar recreación del contenedor con un timestamp único
        $timestamp = Get-Date -Format "yyyyMMddHHmmss"
        Write-Host "Forzando actualización con timestamp: $timestamp" -ForegroundColor Yellow
        
        # Actualizar con revisión específica para forzar rebuild
        Write-Host "Actualizando Container App..." -ForegroundColor Yellow
        try {
            $result = az containerapp update --name $DashboardApp --resource-group $ResourceGroup --image "ghcr.io/dygsom/dygsom-fraud-dashboard:main" --revision-suffix "update$timestamp" --output json | ConvertFrom-Json
            
            if ($result) {
                Write-Host "Dashboard actualizado exitosamente!" -ForegroundColor Green
                Write-Host "Nueva revision: $($result.properties.latestRevisionName)" -ForegroundColor Green
                
                Write-Host ""
                Write-Host "Esperando 30 segundos para que se inicialice..." -ForegroundColor Yellow
                Start-Sleep -Seconds 30
                
                Write-Host ""
                Write-Host "Verificando logs del dashboard actualizado..." -ForegroundColor Yellow
                az containerapp logs show --name $DashboardApp --resource-group $ResourceGroup --tail 10
            }
        } catch {
            Write-Host "Error durante la actualización: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host ""
        Write-Host "No se requiere actualización. El dashboard está sincronizado." -ForegroundColor Green
        Write-Host ""
        Write-Host "Para forzar una actualización, usa: .\update-dashboard.ps1 -ForceUpdate" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Error obteniendo información del repositorio: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Set-Location $currentDir
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "  URLS DE ACCESO" -ForegroundColor Blue  
Write-Host "================================================================================" -ForegroundColor Blue
Write-Host "Dashboard: https://app.dygsom.pe" -ForegroundColor Blue
Write-Host "Container URL: https://ca-dashboard-dev.bravetree-275a9744.brazilsouth.azurecontainerapps.io" -ForegroundColor Blue