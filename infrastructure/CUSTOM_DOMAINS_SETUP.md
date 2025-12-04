# 🌐 CONFIGURACIÓN DE DOMINIOS PERSONALIZADOS

**Objetivo**: Configurar `api.dygsom.pe` y `app.dygsom.pe` con SSL gratuito
**Estado**: ✅ COMPLETADO - Dominios configurados y funcionando
**SSL**: ✅ Azure Managed Certificates (gratuito) - ACTIVO

---

## 🔧 **PASO 1: CONFIGURAR DNS EN GODADDY**

### Registros DNS Requeridos

Agrega estos registros en tu panel de GoDaddy:

```dns
# CNAME Records (ya configurados ✅)
api    CNAME    ca-api-dev.bravetree-275a9744.brazilsouth.azurecontainerapps.io
app    CNAME    ca-dashboard-dev.bravetree-275a9744.brazilsouth.azurecontainerapps.io

# TXT Records para validación (NUEVOS - agregar estos) ⚠️
asuid.api    TXT    7A19DBACCC51168EC06D506AC2B54CC571ADB9B6ADB2505A2DF93F9B14E83BCD
asuid.app    TXT    7A19DBACCC51168EC06D506AC2B54CC571ADB9B6ADB2505A2DF93F9B14E83BCD
```

### Screenshots de Configuración GoDaddy

1. Ve a **DNS Management** en tu dominio `dygsom.pe`
2. Agrega estos **2 nuevos registros TXT**:

| Tipo | Host | Valor |
|------|------|-------|
| TXT | `asuid.api` | `7A19DBACCC51168EC06D506AC2B54CC571ADB9B6ADB2505A2DF93F9B14E83BCD` |
| TXT | `asuid.app` | `7A19DBACCC51168EC06D506AC2B54CC571ADB9B6ADB2505A2DF93F9B14E83BCD` |

⏱️ **Tiempo de propagación**: 5-15 minutos

---

## 🔧 **PASO 2: COMANDOS AZURE (Ejecutar después del DNS)**

### Una vez que agregues los TXT records, ejecuta:

```bash
# 1. Agregar dominio personalizado para API
az containerapp hostname add \
  --hostname api.dygsom.pe \
  --name ca-api-dev \
  --resource-group rg-dygsom-fraud-mvp

# 2. Agregar dominio personalizado para Dashboard  
az containerapp hostname add \
  --hostname app.dygsom.pe \
  --name ca-dashboard-dev \
  --resource-group rg-dygsom-fraud-mvp

# 3. Bind SSL certificate gratuito para API
az containerapp hostname bind \
  --hostname api.dygsom.pe \
  --name ca-api-dev \
  --resource-group rg-dygsom-fraud-mvp \
  --environment cae-dygsom-dev

# 4. Bind SSL certificate gratuito para Dashboard
az containerapp hostname bind \
  --hostname app.dygsom.pe \
  --name ca-dashboard-dev \
  --resource-group rg-dygsom-fraud-mvp \
  --environment cae-dygsom-dev
```

---

## 🎯 **RESULTADO ESPERADO**

### URLs Finales:
- **API**: https://api.dygsom.pe/docs (Swagger UI)
- **Dashboard**: https://app.dygsom.pe (Frontend)

### URLs Originales (seguirán funcionando):
- **API**: https://ca-api-dev.bravetree-275a9744.brazilsouth.azurecontainerapps.io/docs
- **Dashboard**: https://ca-dashboard-dev.bravetree-275a9744.brazilsouth.azurecontainerapps.io

### SSL Certificate:
✅ **Gratuito** - Azure Managed Certificates
✅ **Renovación automática** 
✅ **Trusted CA** - DigiCert/Let's Encrypt

---

## ✅ **VALIDACIÓN**

### Paso 1: Verificar DNS propagación
```bash
# Verificar CNAME
nslookup api.dygsom.pe
nslookup app.dygsom.pe

# Verificar TXT records
nslookup -type=TXT asuid.api.dygsom.pe
nslookup -type=TXT asuid.app.dygsom.pe
```

### Paso 2: Test endpoints
```bash
# API Health Check
curl https://api.dygsom.pe/health

# API Documentation  
curl https://api.dygsom.pe/docs

# Dashboard
curl https://app.dygsom.pe
```

---

## 🔄 **ACTUALIZAR CI/CD**

Una vez configurados los dominios, actualizar CORS para permitir el nuevo dominio:

```bash
# Actualizar CORS en API para permitir app.dygsom.pe
az containerapp update \
  --name ca-api-dev \
  --resource-group rg-dygsom-fraud-mvp \
  --set-env-vars DATABASE_URL="secretref:database-url" \
  --ingress-allowed-origins "https://app.dygsom.pe,https://ca-dashboard-dev.bravetree-275a9744.brazilsouth.azurecontainerapps.io,http://localhost:3001"
```

---

## 🎉 **BENEFICIOS**

### Profesionalismo
- ✅ URLs amigables: `api.dygsom.pe` vs `ca-api-dev.bravetree-275a9744.brazilsouth.azurecontainerapps.io`
- ✅ Branding consistente con tu dominio
- ✅ Fácil de recordar para usuarios/clientes

### SSL Gratuito
- ✅ **Costo**: $0/mes (Azure Managed Certificates)
- ✅ **Renovación**: Automática cada 90 días
- ✅ **Trusted**: Certificado validado por CA reconocida

### Compatibilidad
- ✅ **Sin downtime**: URLs originales siguen funcionando
- ✅ **Gradual**: Puedes migrar usuarios gradualmente
- ✅ **Rollback**: Fácil revertir si hay problemas

---

## 📋 **CHECKLIST**

### DNS Configuration (en GoDaddy) ✅ COMPLETADO
- [x] TXT record: `asuid.api.dygsom.pe` → `7A19DBACCC51168EC06D506AC2B54CC571ADB9B6ADB2505A2DF93F9B14E83BCD`
- [x] TXT record: `asuid.app.dygsom.pe` → `7A19DBACCC51168EC06D506AC2B54CC571ADB9B6ADB2505A2DF93F9B14E83BCD`
- [x] Verificar propagación DNS (5-15 min)

### Azure Configuration (después del DNS) ✅ COMPLETADO
- [x] `az containerapp hostname add` para API ✅
- [x] `az containerapp hostname add` para Dashboard ✅
- [x] `az containerapp hostname bind` para SSL API ✅
- [x] `az containerapp hostname bind` para SSL Dashboard ✅
- [x] Actualizar CORS configuration ✅

### Validation ✅ COMPLETADO
- [x] Test `https://api.dygsom.pe/health` → ✅ {"status":"healthy"}
- [x] Test `https://api.dygsom.pe/docs` → ✅ Swagger UI funcional
- [x] Test `https://app.dygsom.pe` → ✅ Dashboard cargando
- [x] Verificar SSL certificate (🔒 en browser) → ✅ Certificados válidos

---

**⏰ Tiempo total estimado**: 30-45 minutos (incluyendo propagación DNS)
**💰 Costo adicional**: $0 (SSL gratuito de Azure)
**🔄 Downtime**: 0 minutos (URLs originales siguen funcionando)

---

*Una vez que agregues los TXT records en GoDaddy, avísame para ejecutar los comandos de Azure* ✅