# 🚀 DYGSOM Fraud Detection - MVP Deployment Guide

**Arquitectura**: Container Apps Simplificado
**Costo estimado**: $45-50 USD/mes
**Región**: brazilsouth (São Paulo, Brasil)
**Latencia desde Lima**: ~30-40ms
**Última actualización**: 2025-12-03

---

## 📊 Análisis de Latencia para Lima, Perú

### Regiones Azure Evaluadas

| Región Azure | Ubicación | Latencia desde Lima | Disponibilidad | Recomendación |
|--------------|-----------|---------------------|----------------|---------------|
| **brazilsouth** ⭐ | São Paulo, Brasil | **~30-40ms** | ✅ Validada | **RECOMENDADO** |
| southcentralus | Texas, USA | ~60-80ms | ✅ Disponible | Alternativa |
| westus2 | Washington, USA | ~100-120ms | ✅ Disponible | No recomendado |
| eastus | Virginia, USA | ~120-140ms | ❌ Restringida | Bloqueada |
| eastus2 | Virginia, USA | ~120-140ms | ❌ Restringida | Bloqueada |

### Justificación: brazilsouth

1. **Latencia óptima**: 30-40ms desde Lima (imperceptible para usuarios)
2. **Disponibilidad validada**: PostgreSQL y Container Apps disponibles
3. **Proximidad geográfica**: ~3,100 km de Lima
4. **Compliance LATAM**: Datos permanecen en América Latina
5. **Costo competitivo**: Sin sobrecosto por región

---

## 🏗️ Arquitectura MVP

```
┌─────────────────────────────────────────────────────────┐
│         Container Apps Environment (Shared)             │
│  ┌────────────────────┐    ┌──────────────────────┐    │
│  │ API Container App  │    │ Dashboard Container  │    │
│  │ - FastAPI          │◄───│ - Next.js            │    │
│  │ - Port 3000        │    │ - Port 3001          │    │
│  │ - Auto-scale 1-5   │    │ - Auto-scale 1-3     │    │
│  │ - 0.5 vCPU, 1GB    │    │ - 0.25 vCPU, 0.5GB   │    │
│  └────────────────────┘    └──────────────────────┘    │
│            │                         │                   │
│            └────────┬────────────────┘                   │
│                     ▼                                    │
│         ┌──────────────────────┐                         │
│         │ PostgreSQL Flexible  │                         │
│         │ - Version 15         │                         │
│         │ - Burstable B1ms     │                         │
│         │ - 1 vCore, 2GB RAM   │                         │
│         │ - 32GB Storage       │                         │
│         │ - 7-day backups      │                         │
│         └──────────────────────┘                         │
│                                                           │
│         ┌──────────────────────┐                         │
│         │ Redis Basic C0       │                         │
│         │ - 250MB cache        │                         │
│         │ - SSL only           │                         │
│         │ - Optional ($16/mes) │                         │
│         └──────────────────────┘                         │
└─────────────────────────────────────────────────────────┘
```

### Características de Confiabilidad y Escalabilidad

✅ **Auto-scaling**:
- API: 1-5 replicas (30 concurrent requests → scale up)
- Dashboard: 1-3 replicas (50 concurrent requests → scale up)

✅ **Health Probes**:
- Liveness: `/health` (cada 30s)
- Readiness: `/health/ready` (cada 10s)
- Auto-restart en caso de falla

✅ **Backups Automáticos**:
- PostgreSQL: 7 días de retención
- Restore point-in-time

✅ **Alta Disponibilidad**:
- minReplicas: 1 (sin cold starts)
- maxReplicas configurado para crecimiento

✅ **Seguridad**:
- HTTPS only (TLS 1.2+)
- PostgreSQL con SSL requerido
- Redis con SSL only
- CORS configurado correctamente

---

## 📋 Pre-requisitos Completos

### 1. Herramientas Locales

```bash
# Azure CLI
az --version  # Debe ser >= 2.50.0
# Instalar: https://learn.microsoft.com/cli/azure/install-azure-cli

# Docker Desktop (para validar imágenes localmente - opcional)
docker --version  # Debe ser >= 20.10.0
# Instalar: https://www.docker.com/products/docker-desktop/

# Git (para commits)
git --version  # Debe ser >= 2.30.0
```

### 2. Cuenta y Suscripción Azure

```bash
# Login a Azure
az login

# Verificar suscripción activa
az account show

# Cambiar suscripción si es necesario
az account set --subscription "310c76ca-e06c-45ae-a56e-2d0f7b6e5dae"

# Verificar que tienes permisos de Owner o Contributor
az role assignment list --assignee $(az account show --query user.name -o tsv) --all
```

### 3. GitHub - Imágenes Docker Públicas

**Imágenes requeridas**:
- `ghcr.io/dygsom/dygsom-fraud-api:main` ✅
- `ghcr.io/dygsom/dygsom-fraud-dashboard:main` ⏳

**Estado actual**:
- ✅ API: Workflow configurado, imagen construida
- ⏳ Dashboard: Workflow creado, pendiente push

**Pasos para hacer imágenes públicas**:

1. Ve a: https://github.com/dygsom?tab=packages
2. Para cada package (dygsom-fraud-api, dygsom-fraud-dashboard):
   - Haz clic en el package
   - **Package settings** (lado derecho)
   - Scroll hasta **"Danger Zone"**
   - **Change visibility** → **Public**
   - Confirma el nombre del package

### 4. Validación de Región

```bash
# Verificar que brazilsouth tiene todos los servicios
az provider show --namespace Microsoft.App --query "resourceTypes[?resourceType=='managedEnvironments'].locations" -o table
az provider show --namespace Microsoft.DBforPostgreSQL --query "resourceTypes[?resourceType=='flexibleServers'].locations" -o table

# Debe aparecer "Brazil South" en ambos
```

### 5. Resource Providers (Registro automático)

```bash
# Registrar providers necesarios (solo primera vez)
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.DBforPostgreSQL
az provider register --namespace Microsoft.Cache
az provider register --namespace Microsoft.OperationalInsights

# Verificar estado (debe estar "Registered")
az provider show --namespace Microsoft.App --query "registrationState"
```

---

## 🚀 Pasos de Deployment

### Paso 1: Commit del Workflow del Dashboard

```bash
# En el repo del dashboard
cd D:\code\dygsom\dygsom-fraud-dashboard

# Verificar workflow creado
ls .github/workflows/docker-build-push.yml

# Add, commit y push
git add .github/workflows/docker-build-push.yml
git commit -m "feat: Add Docker build workflow for dashboard

- Build multi-arch image (amd64, arm64)
- Push to GHCR automatically
- Enable auto-deployment to Azure

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### Paso 2: Monitorear Build del Dashboard

```bash
# El workflow se activará automáticamente
# Monitorear en: https://github.com/dygsom/dygsom-fraud-dashboard/actions

# Esperar ~5-10 minutos para que complete
# Debe aparecer check verde ✅
```

### Paso 3: Hacer Imágenes Públicas

**API**:
1. https://github.com/dygsom?tab=packages
2. Click en **dygsom-fraud-api**
3. Package settings → Change visibility → **Public**

**Dashboard**:
1. Esperar a que termine el build
2. https://github.com/dygsom?tab=packages
3. Click en **dygsom-fraud-dashboard**
4. Package settings → Change visibility → **Public**

### Paso 4: Validar Imágenes Accesibles

```bash
# Probar pull de imágenes (sin autenticación)
docker pull ghcr.io/dygsom/dygsom-fraud-api:main
docker pull ghcr.io/dygsom/dygsom-fraud-dashboard:main

# Si funciona, están públicas ✅
```

### Paso 5: Crear Resource Group

```bash
cd D:\code\dygsom\dygsom-fraud-api\infrastructure

# Crear resource group en brazilsouth
az group create \
  --name rg-dygsom-fraud-mvp \
  --location brazilsouth \
  --tags Environment=MVP Project=FraudDetection Owner=DYGSOM

# Verificar creación
az group show --name rg-dygsom-fraud-mvp
```

### Paso 6: Validar Template Bicep

```bash
# Validar sintaxis y recursos
az deployment group validate \
  --resource-group rg-dygsom-fraud-mvp \
  --template-file dygsom-fraud-mvp.bicep \
  --parameters @dygsom-fraud-mvp.parameters.json

# Si no hay errores, continuar ✅
# Si hay errores, revisar output y corregir
```

### Paso 7: Desplegar Infraestructura

```bash
# Deployment completo (toma ~12-15 minutos)
az deployment group create \
  --resource-group rg-dygsom-fraud-mvp \
  --template-file dygsom-fraud-mvp.bicep \
  --parameters @dygsom-fraud-mvp.parameters.json \
  --name "dygsom-mvp-$(date +%Y%m%d-%H%M%S)" \
  --verbose

# Monitorear progreso en Azure Portal:
# https://portal.azure.com/#view/HubsExtension/DeploymentDetailsBlade/~/overview/id/%2Fsubscriptions%2F310c76ca-e06c-45ae-a56e-2d0f7b6e5dae%2FresourceGroups%2Frg-dygsom-fraud-mvp
```

### Paso 8: Obtener URLs de Salida

```bash
# Obtener todas las URLs
az deployment group show \
  --resource-group rg-dygsom-fraud-mvp \
  --name dygsom-mvp-TIMESTAMP \
  --query properties.outputs

# Outputs esperados:
# - apiUrl: https://ca-api-dev.xxx.brazilsouth.azurecontainerapps.io
# - dashboardUrl: https://ca-dashboard-dev.xxx.brazilsouth.azurecontainerapps.io
# - apiSwaggerUrl: https://ca-api-dev.xxx.brazilsouth.azurecontainerapps.io/docs
```

### Paso 9: Verificar Health Checks

```bash
# Verificar API
curl https://ca-api-dev.xxx.brazilsouth.azurecontainerapps.io/health
# Esperado: {"status":"healthy"}

# Verificar Dashboard
curl https://ca-dashboard-dev.xxx.brazilsouth.azurecontainerapps.io
# Esperado: HTML de la página

# Verificar Swagger
open https://ca-api-dev.xxx.brazilsouth.azurecontainerapps.io/docs
```

### Paso 10: Ejecutar Migraciones de Base de Datos

```bash
# Obtener nombre del Container App
API_APP_NAME=$(az containerapp list \
  --resource-group rg-dygsom-fraud-mvp \
  --query "[?contains(name, 'api')].name" -o tsv)

# Ejecutar migraciones de Prisma
az containerapp exec \
  --resource-group rg-dygsom-fraud-mvp \
  --name $API_APP_NAME \
  --command "prisma migrate deploy"

# Verificar tablas creadas
az containerapp exec \
  --resource-group rg-dygsom-fraud-mvp \
  --name $API_APP_NAME \
  --command "prisma db pull"
```

---

## 🧪 Testing Post-Deployment

### Test 1: API Health Check

```bash
API_URL="https://ca-api-dev.xxx.brazilsouth.azurecontainerapps.io"

# Health básico
curl $API_URL/health

# Readiness check
curl $API_URL/health/ready

# Swagger docs
curl $API_URL/docs
```

### Test 2: Dashboard Access

```bash
DASHBOARD_URL="https://ca-dashboard-dev.xxx.brazilsouth.azurecontainerapps.io"

# Página principal
curl -I $DASHBOARD_URL
# Esperado: HTTP/2 200

# Login page
curl -I $DASHBOARD_URL/login
```

### Test 3: API Fraud Scoring

```bash
# Crear API key de prueba (desde dashboard o psql)
# Luego:

curl -X POST $API_URL/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu-api-key-aqui" \
  -d '{
    "transaction_id": "test-001",
    "amount": 150.50,
    "currency": "PEN",
    "customer_email": "test@example.com",
    "customer_ip": "8.8.8.8",
    "merchant_id": "merchant-123",
    "payment_method": "credit_card"
  }'

# Esperado: { "fraud_score": ..., "risk_level": ..., "recommendation": ... }
```

### Test 4: Latencia desde Lima

```bash
# Medir latencia real
for i in {1..10}; do
  curl -w "Time: %{time_total}s\n" -o /dev/null -s $API_URL/health
done

# Promedio esperado: 0.03-0.04s (30-40ms) ✅
```

---

## 💰 Costos Mensuales Estimados

### Desglose por Servicio

| Servicio | SKU | Uso Estimado | Costo/Mes |
|----------|-----|--------------|-----------|
| **Container Apps** | 0.75 vCPU, 1.5GB | 730 hrs/mes, low traffic | $25-35 |
| **PostgreSQL Flexible** | Burstable B1ms | 730 hrs/mes | $15 |
| **Redis Basic** | C0, 250MB | 730 hrs/mes | $16 |
| **Log Analytics** | PerGB2018 | ~2GB/mes | $5 |
| **TOTAL** | | | **$61/mes** |

### Opciones de Ahorro

1. **Deshabilitar Redis** (-$16/mes):
   ```json
   "enableRedis": { "value": false }
   ```
   Total: $45/mes

2. **Reducir Log Retention** (30 → 7 días) (-$3/mes):
   - Editar Bicep línea 66: `retentionInDays: 7`
   - Total: $58/mes

3. **Ambas optimizaciones**:
   - Total: $42/mes ✅ (mínimo viable)

---

## 🔧 Troubleshooting

### Error: "Image pull failed"

```bash
# Verificar que imagen es pública
curl -I https://ghcr.io/v2/dygsom/dygsom-fraud-api/manifests/main

# Si devuelve 404, la imagen no existe
# Si devuelve 401, la imagen no es pública
```

**Solución**: Hacer imagen pública en GitHub Packages

### Error: "LocationNotAvailableForResourceType"

```bash
# Cambiar región en parameters.json
"location": { "value": "southcentralus" }
```

### Error: "Database connection failed"

```bash
# Verificar firewall de PostgreSQL permite Azure services
az postgres flexible-server firewall-rule list \
  --resource-group rg-dygsom-fraud-mvp \
  --name pg-dygsom-dev

# Debe existir regla "AllowAllAzureServicesAndResourcesWithinAzureIps"
```

### Logs de Container App

```bash
# Ver logs en tiempo real
az containerapp logs show \
  --resource-group rg-dygsom-fraud-mvp \
  --name ca-api-dev \
  --follow

# Logs recientes
az containerapp logs show \
  --resource-group rg-dygsom-fraud-mvp \
  --name ca-api-dev \
  --tail 100
```

---

## 🔄 Actualización de Imágenes

### Deployment automático con nuevas imágenes

```bash
# Push a main en cualquier repo activa workflow
# GitHub Actions construye y publica nueva imagen
# Container Apps NO se actualiza automáticamente

# Para actualizar Container Apps con nueva imagen:
az containerapp update \
  --resource-group rg-dygsom-fraud-mvp \
  --name ca-api-dev \
  --image ghcr.io/dygsom/dygsom-fraud-api:main

# O re-ejecutar deployment completo
az deployment group create \
  --resource-group rg-dygsom-fraud-mvp \
  --template-file dygsom-fraud-mvp.bicep \
  --parameters @dygsom-fraud-mvp.parameters.json \
  --name "dygsom-mvp-update-$(date +%Y%m%d-%H%M%S)"
```

---

## 📊 Monitoreo y Métricas

### Azure Portal

1. **Container Apps**:
   - Metrics: CPU, Memory, Requests/sec, Response time
   - Logs: Application logs, System logs
   - Revisions: Historial de deployments

2. **PostgreSQL**:
   - Metrics: Connections, Storage, CPU
   - Backups: Restore points disponibles

3. **Redis**:
   - Metrics: Cache hits/misses, Memory usage
   - Operations: Get/Set performance

### Log Analytics Queries (Kusto)

```kusto
// Errores en los últimos 30 minutos
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(30m)
| where Log_s contains "ERROR"
| project TimeGenerated, ContainerAppName_s, Log_s
| order by TimeGenerated desc

// Latencia promedio de requests
ContainerAppConsoleLogs_CL
| where Log_s contains "request_time"
| summarize avg(todouble(extract("request_time=(\\d+\\.?\\d*)", 1, Log_s))) by bin(TimeGenerated, 5m)
```

---

## ✅ Checklist de Deployment

- [ ] Azure CLI instalado y autenticado
- [ ] Suscripción Azure validada
- [ ] Resource providers registrados
- [ ] Workflow del Dashboard creado y pusheado
- [ ] Build del Dashboard completado (✅ en GitHub Actions)
- [ ] Imagen API pública en GHCR
- [ ] Imagen Dashboard pública en GHCR
- [ ] Imágenes validadas con `docker pull`
- [ ] Resource group creado en brazilsouth
- [ ] Template Bicep validado
- [ ] Deployment ejecutado (12-15 min)
- [ ] URLs obtenidas de outputs
- [ ] Health checks pasando
- [ ] Migraciones ejecutadas
- [ ] Test de fraud scoring exitoso
- [ ] Latencia validada (<50ms)
- [ ] Dashboard accesible y funcional

---

## 📞 Soporte

**Documentación**:
- Azure Container Apps: https://learn.microsoft.com/azure/container-apps/
- PostgreSQL Flexible: https://learn.microsoft.com/azure/postgresql/flexible-server/
- GitHub Packages: https://docs.github.com/packages

**Issues Conocidos**:
- Ver: `infrastructure/SESION_DEPLOYMENT_AZURE.md`
- Ver: `infrastructure/BICEP_FIXES_CHANGELOG.md`

---

**Última actualización**: 2025-12-03
**Versión**: MVP 1.0
**Arquitectura**: Container Apps Simplificado
**Región**: brazilsouth
**Costo**: $45-61/mes
