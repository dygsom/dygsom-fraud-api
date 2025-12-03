# DYGSOM Fraud Detection - Azure Infrastructure

Infraestructura como código (IaC) para desplegar la API y Dashboard en Azure.

---

## 📁 Estructura de Archivos

```
infrastructure/
├── dygsom-fraud-main.bicep              # Plantilla Bicep corregida
├── dygsom-fraud-main.parameters.json    # Parámetros de ejemplo
├── BICEP_FIXES_CHANGELOG.md             # Changelog detallado de correcciones
└── README.md                             # Este archivo
```

---

## 🏗️ Arquitectura Desplegada

```
┌─────────────────────────────────────────────────────────────────┐
│                       Resource Group                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                              │ │
│  │  ┌──────────────────┐         ┌──────────────────┐         │ │
│  │  │  App Service B1  │         │ Container Apps   │         │ │
│  │  │  (Next.js        │────────▶│ (FastAPI)        │         │ │
│  │  │   Dashboard)     │   API   │ Port 3000        │         │ │
│  │  └──────────────────┘  Calls  └──────────────────┘         │ │
│  │                                        │                     │ │
│  │                                        │                     │ │
│  │                    ┌───────────────────┴─────────────┐      │ │
│  │                    ▼                                 ▼      │ │
│  │         ┌─────────────────────┐         ┌──────────────┐   │ │
│  │         │ PostgreSQL 15       │         │ Redis Basic  │   │ │
│  │         │ Flexible Server     │         │ C0 (Cache)   │   │ │
│  │         │ Burstable B1ms      │         └──────────────┘   │ │
│  │         └─────────────────────┘                             │ │
│  │                                                              │ │
│  │  ┌──────────────────┐  ┌──────────────────┐                │ │
│  │  │ Key Vault        │  │ App Insights     │                │ │
│  │  │ (Secrets)        │  │ + Log Analytics  │                │ │
│  │  └──────────────────┘  └──────────────────┘                │ │
│  │                                                              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Componentes**:
- **Container Apps**: API FastAPI (auto-scaling 1-5 replicas)
- **App Service**: Dashboard Next.js (B1 Linux)
- **PostgreSQL 15**: Database (Burstable B1ms, 32GB)
- **Redis**: Caché L2 (Basic C0)
- **Key Vault**: Gestión de secretos
- **Application Insights**: Monitoring & telemetry
- **Log Analytics**: Logs centralizados

---

## 🚀 Despliegue Rápido (Quick Start)

### Prerrequisitos

1. **Azure CLI** instalado ([Instrucciones](https://learn.microsoft.com/cli/azure/install-azure-cli))
2. **Suscripción de Azure** activa
3. **Docker image** de la API publicada en registro público (GHCR, Docker Hub) o Azure Container Registry
4. **Cuenta de GitHub/GitLab** (opcional para CI/CD)

---

### Paso 1: Login a Azure

```bash
az login
az account set --subscription "310c76ca-e06c-45ae-a56e-2d0f7b6e5dae"
#az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

---

### Paso 2: Crear Resource Group

```bash
# Cambiar región si es necesario (eastus, westeurope, etc.)
az group create --name rg-dygsom-fraud-dev --location eastus
```

---

### Paso 3: Editar Parámetros

Edita `dygsom-fraud-main.parameters.json`:

```json
{
  "parameters": {
    "location": {
      "value": "eastus"  // ← Tu región
    },
    "envName": {
      "value": "dev"  // dev, qa, prod
    },
    "postgresAdminUser": {
      "value": "pgadmin"
    },
    "postgresAdminPassword": {
      "value": "CHANGE_ME_STRONG_PASSWORD_123!"  // ← Password fuerte
    },
    "apiImage": {
      "value": "ghcr.io/TU_ORG/dygsom-fraud-api:latest"  // ← Tu imagen
    },
    "postgresDatabaseName": {
      "value": "dygsom_fraud"
    },
    "appServiceSku": {
      "value": "B1"  // B1 (MVP) o S1 (prod)
    },
    "appServiceTier": {
      "value": "Basic"  // Basic o Standard
    }
  }
}
```

**⚠️ IMPORTANTE**:
- `postgresAdminPassword`: Mínimo 8 caracteres, letras + números + símbolos
- `apiImage`: Debe ser una imagen pública o configurar ACR authentication

---

### Paso 4: Validar Template

```bash
az deployment group validate --resource-group rg-dygsom-fraud-dev --template-file dygsom-fraud-main.bicep --parameters @dygsom-fraud-main.parameters.json
```

Si hay errores, revisar output y corregir.

---

### Paso 5: Desplegar Infraestructura

```bash
az deployment group create \
  --resource-group rg-dygsom-fraud-dev \
  --template-file dygsom-fraud-main.bicep \
  --parameters @dygsom-fraud-main.parameters.json \
  --name dygsom-fraud-deployment-$(date +%Y%m%d-%H%M%S)
```

**Tiempo estimado**: 10-15 minutos.

---

### Paso 6: Obtener URLs

```bash
# Dashboard URL
az deployment group show \
  --resource-group rg-dygsom-fraud-dev \
  --name dygsom-fraud-deployment-TIMESTAMP \
  --query properties.outputs.dashboardUrl.value -o tsv

# API URL
az deployment group show \
  --resource-group rg-dygsom-fraud-dev \
  --name dygsom-fraud-deployment-TIMESTAMP \
  --query properties.outputs.apiUrl.value -o tsv
```

O ver todos los outputs:

```bash
az deployment group show \
  --resource-group rg-dygsom-fraud-dev \
  --name dygsom-fraud-deployment-TIMESTAMP \
  --query properties.outputs
```

---

### Paso 7: Ejecutar Migraciones de Base de Datos

Una vez desplegada la infraestructura, ejecutar migraciones de Prisma:

**Opción A: Desde Container App (recomendado)**

```bash
# Obtener nombre de Container App
CONTAINER_APP_NAME=$(az containerapp list \
  --resource-group rg-dygsom-fraud-dev \
  --query "[0].name" -o tsv)

# Ejecutar comando en Container App
az containerapp exec \
  --resource-group rg-dygsom-fraud-dev \
  --name $CONTAINER_APP_NAME \
  --command "/bin/sh -c 'prisma migrate deploy'"
```

**Opción B: Desde local (requiere DATABASE_URL)**

```bash
# Obtener DATABASE_URL del deployment
DATABASE_URL=$(az deployment group show \
  --resource-group rg-dygsom-fraud-dev \
  --name dygsom-fraud-deployment-TIMESTAMP \
  --query "properties.outputs.databaseUrl.value" -o tsv)

# Exportar y ejecutar
export DATABASE_URL="$DATABASE_URL"
npx prisma migrate deploy
```

---

### Paso 8: Seed Database (Opcional)

```bash
az containerapp exec \
  --resource-group rg-dygsom-fraud-dev \
  --name $CONTAINER_APP_NAME \
  --command "/bin/sh -c 'python -m src.scripts.seed_transactions'"
```

---

### Paso 9: Verificar Deployment

```bash
# Health check de la API
curl https://<API_URL>/health

# Readiness check
curl https://<API_URL>/health/ready

# Swagger docs
open https://<API_URL>/docs
```

**Respuesta esperada** (`/health`):
```json
{
  "status": "healthy",
  "timestamp": "2025-11-29T10:00:00Z",
  "version": "1.0.0"
}
```

---

## 🔐 Configuración Post-Deployment

### 1. Configurar Custom Domains (Opcional)

```bash
# Dashboard
az webapp config hostname add \
  --resource-group rg-dygsom-fraud-dev \
  --webapp-name app-dygsom-fraud-dev \
  --hostname fraud.tudominio.com

# API (Container Apps requiere configuración manual en portal)
```

### 2. Configurar SSL Certificates

```bash
# App Service (Managed Certificate - Gratis)
az webapp config ssl create \
  --resource-group rg-dygsom-fraud-dev \
  --name app-dygsom-fraud-dev \
  --hostname fraud.tudominio.com
```

### 3. Actualizar CORS con Dominio Custom

Si configuraste custom domain, actualizar variable de ambiente:

```bash
az containerapp update \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --set-env-vars "CORS_ORIGINS=https://fraud.tudominio.com,http://localhost:3001"
```

---

## 📊 Monitoreo y Logs

### Ver Logs de Container App (API)

```bash
# Logs en tiempo real
az containerapp logs show \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --follow

# Últimos 100 logs
az containerapp logs show \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --tail 100
```

### Ver Logs de App Service (Dashboard)

```bash
# Stream logs
az webapp log tail \
  --resource-group rg-dygsom-fraud-dev \
  --name app-dygsom-fraud-dev

# Descargar logs
az webapp log download \
  --resource-group rg-dygsom-fraud-dev \
  --name app-dygsom-fraud-dev
```

### Application Insights

Acceder a métricas avanzadas en Azure Portal:
1. Resource Group → Application Insights → `appi-dygsom-dev`
2. Ver **Live Metrics**, **Failures**, **Performance**, **Logs**

Queries útiles (Log Analytics):

```kusto
// Errores en los últimos 30 minutos
traces
| where severityLevel >= 3
| where timestamp > ago(30m)
| project timestamp, message, severityLevel
| order by timestamp desc

// Latencia p95 por endpoint
requests
| where timestamp > ago(1h)
| summarize p95=percentile(duration, 95) by name
| order by p95 desc

// Fraud score distribution
customMetrics
| where name == "fraud_score"
| summarize count() by bin(value, 0.1)
```

---

## 🔄 Actualización de Código

### Actualizar API (Nueva Imagen Docker)

```bash
# Opción 1: Update directo
az containerapp update \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --image ghcr.io/TU_ORG/dygsom-fraud-api:v1.2.0

# Opción 2: Crear nueva revision (Blue-Green)
az containerapp revision copy \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --image ghcr.io/TU_ORG/dygsom-fraud-api:v1.2.0
```

### Actualizar Dashboard (Deploy desde GitHub)

```bash
# Configurar GitHub Actions deployment (una sola vez)
az webapp deployment github-actions add \
  --resource-group rg-dygsom-fraud-dev \
  --name app-dygsom-fraud-dev \
  --repo TU_ORG/dygsom-fraud-dashboard \
  --branch main \
  --runtime node:18

# Luego cada push a main despliega automáticamente
```

---

## 💰 Optimización de Costos

### Ver Costos Actuales

```bash
# Costos del resource group (últimos 30 días)
az consumption usage list \
  --start-date $(date -d "30 days ago" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceName, 'dygsom')]" \
  --output table
```

### Configurar Budget Alerts

```bash
az consumption budget create \
  --resource-group rg-dygsom-fraud-dev \
  --budget-name dygsom-fraud-budget \
  --amount 150 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2026-12-31 \
  --notifications \
    threshold=80 \
    contactEmails='["tu@email.com"]'
```

### Reducir Costos (Dev/QA)

```bash
# Apagar Container Apps fuera de horario (no cobra si minReplicas=0)
az containerapp update \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --min-replicas 0  # Solo para dev, NO para prod

# Apagar App Service fuera de horario
az webapp stop \
  --resource-group rg-dygsom-fraud-dev \
  --name app-dygsom-fraud-dev

# Reanudar
az webapp start \
  --resource-group rg-dygsom-fraud-dev \
  --name app-dygsom-fraud-dev
```

---

## 🧪 Testing en Staging

Crear ambiente de staging con costos mínimos:

```bash
# Deployment a ambiente qa
az deployment group create \
  --resource-group rg-dygsom-fraud-qa \
  --template-file dygsom-fraud-main.bicep \
  --parameters envName=qa \
               apiImage=ghcr.io/TU_ORG/dygsom-fraud-api:staging \
               appServiceSku=B1
```

---

## 🗑️ Limpieza (Cleanup)

**⚠️ PELIGRO**: Esto eliminará TODOS los recursos.

```bash
# Eliminar resource group completo
az group delete \
  --name rg-dygsom-fraud-dev \
  --yes --no-wait

# Verificar eliminación
az group exists --name rg-dygsom-fraud-dev
# Output: false
```

Para eliminar solo un servicio específico:

```bash
# Ejemplo: Eliminar solo Container App
az containerapp delete \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --yes
```

---

## 🐛 Troubleshooting

### Problema: Container App no arranca

**Síntomas**: `az containerapp show` muestra status `Failed`

**Solución**:
```bash
# Ver logs de provisioning
az containerapp logs show \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev

# Verificar que la imagen Docker existe y es pública
docker pull ghcr.io/TU_ORG/dygsom-fraud-api:latest
```

**Causas comunes**:
- Imagen Docker privada sin credentials
- Puerto incorrecto en `targetPort`
- Variables de ambiente faltantes

---

### Problema: Dashboard no puede conectar a API

**Síntomas**: Error CORS en browser console

**Solución**:
```bash
# Verificar CORS_ORIGINS en Container App
az containerapp show \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --query "properties.template.containers[0].env[?name=='CORS_ORIGINS'].value"

# Actualizar si es necesario
az containerapp update \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --set-env-vars "CORS_ORIGINS=https://app-dygsom-fraud-dev.azurewebsites.net"
```

---

### Problema: PostgreSQL connection timeout

**Síntomas**: API logs muestran `connection timeout` o `could not connect to server`

**Solución**:
```bash
# Verificar firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group rg-dygsom-fraud-dev \
  --name pg-dygsom-dev

# Agregar regla si falta
az postgres flexible-server firewall-rule create \
  --resource-group rg-dygsom-fraud-dev \
  --name pg-dygsom-dev \
  --rule-name AllowAll \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 255.255.255.255
```

---

### Problema: Redis authentication failed

**Síntomas**: `NOAUTH Authentication required` en logs

**Solución**:
```bash
# Verificar que REDIS_URL incluye password
az containerapp show \
  --resource-group rg-dygsom-fraud-dev \
  --name ca-dygsom-fraud-api-dev \
  --query "properties.template.containers[0].env[?name=='REDIS_URL'].value"

# Debe ser formato: rediss://:PASSWORD@host:6380/0
```

---

## 📚 Referencias

- [Azure Container Apps Docs](https://learn.microsoft.com/azure/container-apps/)
- [PostgreSQL Flexible Server Docs](https://learn.microsoft.com/azure/postgresql/flexible-server/)
- [Azure Cache for Redis Docs](https://learn.microsoft.com/azure/azure-cache-for-redis/)
- [App Service Docs](https://learn.microsoft.com/azure/app-service/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)

---

## 🆘 Soporte

Para problemas o preguntas:
1. Revisar `BICEP_FIXES_CHANGELOG.md` para entender cambios
2. Verificar Azure Portal → Resource Group → Deployments
3. Consultar Application Insights logs
4. Abrir issue en repositorio del proyecto

---

**Última actualización**: 2025-11-29
**Versión Bicep**: 2.0 (Corregida y Optimizada)
