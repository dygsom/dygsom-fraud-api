# 📋 Sesión de Deployment Azure - DYGSOM Fraud API

**Fecha**: 2025-11-29
**Objetivo**: Desplegar API y Dashboard en Azure usando Bicep
**Estado**: 🟡 En Progreso - Construyendo imagen Docker

---

## 🎯 Contexto del Proyecto

### Arquitectura Objetivo

**Infraestructura Azure**:
- **API**: Azure Container Apps (FastAPI + Python 3.11)
- **Dashboard**: App Service B1 Linux (Next.js - NO EXISTE AÚN)
- **Database**: PostgreSQL 15 Flexible Server (Burstable B1ms, 32GB)
- **Cache**: Azure Cache for Redis (Basic C0, 250MB)
- **Secrets**: Azure Key Vault (RBAC)
- **Monitoring**: Application Insights + Log Analytics
- **Storage**: Storage Account para logs/artifacts

**Región**: `brazilsouth` (São Paulo, Brasil)
**Razón**: Más cercana a Lima, Perú (~30-40ms latencia)

---

## 📁 Estructura del Proyecto

```
dygsom-fraud-api/
├── infrastructure/                          # Bicep templates
│   ├── dygsom-fraud-main.bicep             # ✅ Template corregido
│   ├── dygsom-fraud-main.parameters.json   # ✅ Parámetros configurados
│   ├── deploy.sh / deploy.ps1              # ✅ Scripts de deployment
│   ├── README.md                            # ✅ Documentación completa
│   ├── BICEP_FIXES_CHANGELOG.md            # ✅ Changelog de fixes
│   ├── RESUMEN_EJECUTIVO.md                # ✅ Resumen ejecutivo
│   └── SESION_DEPLOYMENT_AZURE.md          # 📄 Este archivo
├── src/                                     # Código API (FastAPI)
├── Dockerfile                               # ✅ Dockerfile multi-stage
├── docker-compose.yml                       # ✅ Para desarrollo local
├── prisma/schema.prisma                     # ✅ Schema de base de datos
└── .github/workflows/ci.yml                 # ✅ CI pipeline (no publica imagen)
```

---

## 🔧 Problemas Encontrados y Soluciones

### 1. ❌ PostgreSQL - Restricción de Región

**Problema**: Regiones `eastus` y `eastus2` restringidas para PostgreSQL en la suscripción.

**Error**:
```
LocationIsOfferRestricted: Subscriptions are restricted from provisioning
in location 'eastus'. Try again in a different location.
```

**Solución**: ✅ Cambiar a `brazilsouth` (validado con `az postgres flexible-server list-skus`)

---

### 2. ❌ Key Vault - Nombre Inválido

**Problema 1**: `purgeProtectionEnabled: false` no permitido
**Problema 2**: Nombre muy largo (26 chars, máx 24)
**Problema 3**: Key Vault en soft-delete de deployments anteriores

**Soluciones**:
- ✅ Removido `purgeProtectionEnabled` del Bicep
- ✅ Nombre corto: `kv-${uniqueString(resourceGroup().id, envName)}` (16 chars)
- ✅ Nombre único evita conflictos con soft-delete

---

### 3. ❌ Imagen Docker - No Accesible

**Problema**: `ghcr.io/dygsom/dygsom-fraud-api:latest` no existe o es privada

**Error**:
```
DENIED: requested access to the resource is denied
```

**Solución en Progreso**: 🟡 Construir y publicar imagen a GHCR

---

### 4. ✅ Bicep - Warnings de Compatibilidad

**Problemas**:
- Log Analytics: `sku` como propiedad de nivel superior (debe estar en `properties`)
- PostgreSQL: `publicNetworkAccess` es read-only
- Redis: `sku` estructura incorrecta
- `listKeys()` debe usar referencia directa

**Soluciones**: ✅ Todos corregidos en el Bicep

---

## 📊 Estado Actual de la Infraestructura

### Resource Group: `rg-dygsom-fraud-dev`
**Región**: `brazilsouth`
**Estado**: 🗑️ Limpiado (esperando nuevo deployment)

### Deployments Anteriores (Fallidos)
1. **eastus**: Falló por restricción de PostgreSQL
2. **eastus2**: Falló por restricción de PostgreSQL
3. **brazilsouth**: Falló por imagen Docker no accesible + Key Vault

---

## 🐳 Análisis del Código API y Dashboard

### API (FastAPI)

**Estado**: ✅ Código existe

- **Dockerfile**: ✅ Multi-stage (development + production)
- **Puerto**: 3000
- **CI/CD**: ✅ Pipeline completo (lint, test, build, security scan)
- **Imagen Docker**: ❌ NO publicada en GHCR
- **Ubicación**: `D:\code\dygsom\dygsom-fraud-api\`

**Dockerfile**:
```dockerfile
FROM python:3.11-slim AS production
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN prisma generate
EXPOSE 3000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000", "--workers", "4"]
```

### Dashboard (Next.js)

**Estado**: ❌ NO existe

- Solo hay instrucciones de cómo crearlo (`DASHBOARD_WEB_INSTRUCCIONES.md`)
- Es un proyecto separado que debe crearse
- Debe consumir la API de FastAPI

**Stack Planeado**:
- Framework: Next.js 14
- UI: TailwindCSS + shadcn/ui
- Charts: Recharts
- Auth: NextAuth.js

---

## 🎯 Plan Actual de Deployment

### Opción Seleccionada: Construir y Publicar Imagen Real

**Pasos**:

1. ✅ **Crear GitHub Personal Access Token** ← AQUÍ ESTAMOS
   - Tipo: Fine-grained token (más seguro)
   - Permisos: `Packages: Read and write`
   - URL: https://github.com/settings/personal-access-tokens/new

2. ⏳ **Construir Imagen Docker Localmente**
   ```powershell
   cd D:\code\dygsom\dygsom-fraud-api
   docker build --target production -t ghcr.io/dygsom/dygsom-fraud-api:latest .
   ```

3. ⏳ **Login a GHCR**
   ```powershell
   $GITHUB_TOKEN = "github_pat_..."
   $GITHUB_USER = "TU_USERNAME"
   echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
   ```

4. ⏳ **Publicar Imagen a GHCR**
   ```powershell
   docker push ghcr.io/dygsom/dygsom-fraud-api:latest
   ```

5. ⏳ **Hacer Imagen Pública**
   - https://github.com/dygsom?tab=packages
   - dygsom-fraud-api → Settings → Change visibility → Public

6. ⏳ **Desplegar Infraestructura Completa**
   ```powershell
   cd D:\code\dygsom\dygsom-fraud-api\infrastructure

   # Limpiar
   az group delete --name rg-dygsom-fraud-dev --yes --no-wait
   Start-Sleep -Seconds 60

   # Recrear
   az group create --name rg-dygsom-fraud-dev --location brazilsouth

   # Deploy
   az deployment group create `
     --resource-group rg-dygsom-fraud-dev `
     --template-file dygsom-fraud-main.bicep `
     --parameters @dygsom-fraud-main.parameters.json `
     --name dygsom-fraud-$(Get-Date -Format 'yyyyMMdd-HHmmss')
   ```

---

## 📝 Configuración Actual

### Parámetros Bicep (`dygsom-fraud-main.parameters.json`)

```json
{
  "location": "brazilsouth",
  "envName": "dev",
  "postgresAdminUser": "pgadmin",
  "postgresAdminPassword": "Pgpass$321",
  "apiImage": "ghcr.io/dygsom/dygsom-fraud-api:latest",
  "postgresDatabaseName": "dygsom_fraud",
  "appServiceSku": "B1",
  "appServiceTier": "Basic"
}
```

### Suscripción Azure

```
ID: 310c76ca-e06c-45ae-a56e-2d0f7b6e5dae
Nombre: Azure subscription 1
```

### Regiones Validadas para PostgreSQL

| Región | Estado | Latencia desde Lima |
|--------|--------|---------------------|
| eastus | ❌ Restringida | ~120ms |
| eastus2 | ❌ Restringida | ~120ms |
| **brazilsouth** | ✅ **Disponible** | **~30-40ms** ⭐ |
| southcentralus | ✅ Disponible | ~60-80ms |
| westus2 | ✅ Disponible | ~100-120ms |

---

## 🔑 Correcciones Aplicadas al Bicep

### 1. Log Analytics
```bicep
# ❌ ANTES
sku: { name: 'PerGB2018' }
properties: { ... }

# ✅ DESPUÉS
properties: {
  sku: { name: 'PerGB2018' }
  ...
}
```

### 2. Key Vault
```bicep
# ❌ ANTES
name: 'kv-dygsom-${envName}'
purgeProtectionEnabled: false

# ✅ DESPUÉS
name: 'kv-${uniqueString(resourceGroup().id, envName)}'
enableSoftDelete: true
# purgeProtectionEnabled removido
```

### 3. PostgreSQL
```bicep
# ❌ ANTES
version: '14'
network: {
  publicNetworkAccess: 'Enabled'  # read-only
}

# ✅ DESPUÉS
version: '15'
# network removido (público por defecto)
```

### 4. Redis
```bicep
# ❌ ANTES
sku: { name: 'Basic', family: 'C', capacity: 0 }
properties: { ... }

# ✅ DESPUÉS
properties: {
  sku: { name: 'Basic', family: 'C', capacity: 0 }
  ...
}
```

### 5. listKeys References
```bicep
# ❌ ANTES
listKeys(redis.id, '2023-04-01').primaryKey
listKeys(logAnalytics.id, '2022-10-01').primarySharedKey

# ✅ DESPUÉS
redis.listKeys().primaryKey
logAnalytics.listKeys().primarySharedKey
```

---

## 💰 Costos Estimados

**Environment**: DEV (brazilsouth)

| Servicio | SKU | Costo/Mes (USD) |
|----------|-----|-----------------|
| Container Apps | 0.5 vCPU, 1GB, 1-5 replicas | $20-40 |
| App Service | Basic B1 (Linux) | $13 |
| PostgreSQL | Burstable B1ms, 32GB | $15 |
| Redis | Basic C0, 250MB | $16 |
| Log Analytics | ~5GB/mes | $10 |
| App Insights | Ingestion + queries | $5 |
| Key Vault | Standard | $1 |
| Storage | Standard LRS | $2 |
| **TOTAL ESTIMADO** | | **$82-102/mes** |

---

## ⏭️ Próximos Pasos

### Inmediatos (Hoy)

- [ ] Crear GitHub Fine-grained Token
  - Permisos: `Packages: Read and write`
  - Repository: `dygsom-fraud-api`
- [ ] Construir imagen Docker (7 min)
- [ ] Publicar a GHCR (5 min)
- [ ] Hacer imagen pública
- [ ] Desplegar infraestructura (12-15 min)

### Post-Deployment

- [ ] Verificar health: `curl https://<API_URL>/health`
- [ ] Ejecutar migraciones Prisma: `prisma migrate deploy`
- [ ] Verificar Swagger docs: `https://<API_URL>/docs`
- [ ] Seed database (opcional): `python -m src.scripts.seed_transactions`

### Futuro

- [ ] Crear proyecto Dashboard (Next.js)
- [ ] Configurar CI/CD para auto-publicar imágenes
- [ ] Configurar custom domains
- [ ] Implementar VNet para producción
- [ ] Configurar Azure Front Door + WAF

---

## 🆘 Troubleshooting

### Si el Deployment Falla

```powershell
# Ver errores del deployment
az deployment group show `
  --resource-group rg-dygsom-fraud-dev `
  --name DEPLOYMENT_NAME `
  --query "properties.error" -o json

# Ver recursos creados
az resource list --resource-group rg-dygsom-fraud-dev --output table

# Ver logs de Container App
az containerapp logs show `
  --resource-group rg-dygsom-fraud-dev `
  --name ca-dygsom-fraud-api-dev `
  --follow
```

### Errores Comunes

**"Image pull failed"**:
- Verificar que la imagen existe: `docker pull ghcr.io/dygsom/dygsom-fraud-api:latest`
- Verificar que es pública en GitHub Packages

**"LocationIsOfferRestricted"**:
- Cambiar región en parameters.json
- Verificar con: `az postgres flexible-server list-skus --location REGION`

**"VaultNameNotValid"**:
- Nombre debe tener 3-24 caracteres
- Solo alfanuméricos y guiones
- No guiones consecutivos

---

## 📚 Documentación Generada

### Archivos Creados

1. **dygsom-fraud-main.bicep** (460 líneas)
   - Template Bicep corregido y optimizado
   - 16 recursos definidos
   - Health probes, RBAC, firewall rules

2. **dygsom-fraud-main.parameters.json**
   - Parámetros configurados para dev
   - Región: brazilsouth
   - Imagen: ghcr.io/dygsom/dygsom-fraud-api:latest

3. **deploy.sh** + **deploy.ps1**
   - Scripts automatizados de deployment
   - Validación de prerequisitos
   - Manejo de errores

4. **README.md** (500+ líneas)
   - Guía completa de despliegue
   - Troubleshooting
   - Comandos útiles

5. **BICEP_FIXES_CHANGELOG.md**
   - Changelog detallado de 10+ fixes
   - Comparativa antes/después
   - Estimación de costos

6. **RESUMEN_EJECUTIVO.md**
   - Executive summary
   - Checklist de deployment
   - Roadmap

7. **SESION_DEPLOYMENT_AZURE.md** (este archivo)
   - Resumen de la sesión
   - Estado actual
   - Próximos pasos

---

## 🔗 Enlaces Útiles

### Azure
- Portal: https://portal.azure.com
- Resource Group: https://portal.azure.com/#@/resource/subscriptions/310c76ca-e06c-45ae-a56e-2d0f7b6e5dae/resourceGroups/rg-dygsom-fraud-dev/overview
- Container Apps Docs: https://learn.microsoft.com/azure/container-apps/

### GitHub
- Crear Fine-grained Token: https://github.com/settings/personal-access-tokens/new
- Ver Packages: https://github.com/dygsom?tab=packages
- GHCR Docs: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry

### Docker
- GHCR: https://ghcr.io
- Dockerfile Best Practices: https://docs.docker.com/develop/dev-best-practices/

---

## ✅ Checklist de Deployment

### Pre-Deployment
- [x] Azure CLI instalado y autenticado
- [x] Docker Desktop corriendo
- [x] Bicep template validado
- [x] Región validada (brazilsouth)
- [ ] GitHub token creado
- [ ] Imagen Docker construida
- [ ] Imagen publicada a GHCR
- [ ] Imagen configurada como pública

### Deployment
- [ ] Resource group creado
- [ ] Deployment ejecutado
- [ ] 16 recursos creados exitosamente
- [ ] Outputs verificados (URLs, FQDNs)

### Post-Deployment
- [ ] Health check pasando
- [ ] Migraciones ejecutadas
- [ ] Swagger docs accesibles
- [ ] Application Insights recibiendo logs

---

## 🎓 Lecciones Aprendidas

1. **Validar región antes de deployment**: Usar `az postgres flexible-server list-skus`
2. **Nombres de Key Vault**: Máximo 24 caracteres, usar `uniqueString()`
3. **Imagen Docker**: Debe ser pública o configurar registry credentials
4. **Bicep API versions**: Usar versiones correctas para evitar warnings
5. **Fine-grained tokens**: Más seguros que Classic tokens

---

**Última Actualización**: 2025-11-29 18:00 (hora local Perú)
**Estado**: 🟡 Esperando creación de GitHub token para continuar
**Siguiente Paso**: Crear Fine-grained token y construir imagen Docker
