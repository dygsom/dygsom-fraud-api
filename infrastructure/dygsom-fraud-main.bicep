targetScope = 'resourceGroup'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Environment name (e.g. dev, qa, prod)')
@allowed([
  'dev'
  'qa'
  'prod'
  'sandbox'
])
param envName string = 'dev'

@description('Admin username for PostgreSQL Flexible Server')
param postgresAdminUser string = 'pgadmin'

@secure()
@description('Admin password for PostgreSQL Flexible Server')
param postgresAdminPassword string

@description('Docker image for the fraud API (public registry or ACR)')
param apiImage string = 'ghcr.io/dygsom/dygsom-fraud-api:latest'

@description('Name of the PostgreSQL database used by the API')
param postgresDatabaseName string = 'dygsom_fraud'

@description('App Service SKU name for the dashboard')
@allowed([
  'B1'
  'S1'
])
param appServiceSku string = 'B1'

@description('App Service SKU tier')
@allowed([
  'Basic'
  'Standard'
])
param appServiceTier string = 'Basic'

//
// Observability: Log Analytics + Application Insights
//

@description('Log Analytics workspace name')
param logAnalyticsName string = 'law-dygsom-${envName}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

var logAnalyticsSharedKey = logAnalytics.listKeys().primarySharedKey

resource appInsights 'microsoft.insights/components@2020-02-02' = {
  name: 'appi-dygsom-${envName}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    Request_Source: 'rest'
    WorkspaceResourceId: logAnalytics.id
  }
}

//
// Storage account for diagnostics / artifacts (OPTIONAL - can be removed if not needed)
//

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'stgdygsom${uniqueString(resourceGroup().id, envName)}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

//
// Key Vault (RBAC-based) - For secure secret management
//

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'kv-${uniqueString(resourceGroup().id, envName)}'
  location: location
  properties: {
    tenantId: tenant().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

// Store PostgreSQL password in Key Vault
resource postgresPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'postgres-admin-password'
  properties: {
    value: postgresAdminPassword
  }
}

//
// PostgreSQL Flexible Server (cost-optimized, FIXED VERSION)
//

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: 'pg-dygsom-${envName}'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '15'  // ✅ FIX: Upgraded to PostgreSQL 15
    administratorLogin: postgresAdminUser
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    availabilityZone: '1'
  }
}

// ✅ FIX: Add firewall rule for Azure services (Container Apps, App Service)
resource pgFirewallAzureServices 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2022-12-01' = {
  parent: postgres
  name: 'AllowAllAzureServicesAndResourcesWithinAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'  // Special Azure-internal rule
  }
}

// For MVP: Allow all IPs (tighten in production with VNet)
resource pgFirewallAll 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2022-12-01' = {
  parent: postgres
  name: 'AllowAll'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '255.255.255.255'
  }
}

resource postgresDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-12-01' = {
  parent: postgres
  name: postgresDatabaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

//
// Azure Cache for Redis (basic, cost-optimized)
//

resource redis 'Microsoft.Cache/Redis@2023-04-01' = {
  name: 'redis-dygsom-${envName}'
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

//
// Container Apps environment + fraud API Container App
//

resource containerEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-dygsom-${envName}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalyticsSharedKey
      }
    }
  }
}

resource fraudApi 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-dygsom-fraud-api-${envName}'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000  // ✅ FIX: Changed from 8000 to 3000 (API default port)
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      activeRevisionsMode: 'Single'
      dapr: {
        enabled: false
      }
      registries: []
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'fraud-api'
          image: apiImage
          env: [
            // ✅ FIX: Use DATABASE_URL instead of individual vars
            {
              name: 'DATABASE_URL'
              value: 'postgresql://${postgresAdminUser}:${postgresAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${postgresDatabaseName}?sslmode=require'
            }
            // ✅ FIX: Use REDIS_URL with password and SSL
            {
              name: 'REDIS_URL'
              value: 'rediss://:${redis.listKeys().primaryKey}@${redis.properties.hostName}:${redis.properties.sslPort}/0?ssl_cert_reqs=required'
            }
            // ✅ FIX: Add security secrets (generated uniquely per resource group)
            {
              name: 'API_KEY_SALT'
              value: uniqueString(resourceGroup().id, 'api-key-salt', envName)
            }
            {
              name: 'JWT_SECRET'
              value: uniqueString(resourceGroup().id, 'jwt-secret', envName)
            }
            // Environment configuration
            {
              name: 'ENVIRONMENT'
              value: envName
            }
            {
              name: 'LOG_LEVEL'
              value: envName == 'prod' ? 'INFO' : 'DEBUG'
            }
            // ✅ FIX: Add CORS origins (will include dashboard URL)
            {
              name: 'CORS_ORIGINS'
              value: 'https://app-dygsom-fraud-${envName}.azurewebsites.net,http://localhost:3001'
            }
            // Application Insights
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
            {
              name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
              value: appInsights.properties.InstrumentationKey
            }
          ]
          resources: {
            cpu: json('0.5')  // ✅ IMPROVED: Increased from 0.25 for ML workload
            memory: '1Gi'      // ✅ IMPROVED: Increased from 0.5Gi for XGBoost
          }
          probes: [
            // ✅ FIX: Add health probes
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: 3000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/health/ready'
                port: 3000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1  // ✅ FIX: Changed from 0 to avoid cold starts
        maxReplicas: 5  // ✅ IMPROVED: Increased from 3 for better throughput
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '30'  // ✅ IMPROVED: Increased from 10
              }
            }
          }
        ]
      }
    }
  }
}

// ✅ FIX: Grant Container App access to Key Vault
resource kvRoleAssignmentApi 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, fraudApi.id, 'Key Vault Secrets User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: fraudApi.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

//
// App Service Plan + Web App (dashboard)
//

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: 'asp-dygsom-${envName}'
  location: location
  kind: 'linux'
  sku: {
    name: appServiceSku
    tier: appServiceTier
    size: appServiceSku
    capacity: 1
  }
  properties: {
    reserved: true
  }
}

resource dashboardApp 'Microsoft.Web/sites@2022-03-01' = {
  name: 'app-dygsom-fraud-${envName}'
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      alwaysOn: appServiceSku == 'B1' ? false : true  // B1 doesn't support alwaysOn
      http20Enabled: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '~18'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        // ✅ FIX: API URL injected correctly
        {
          name: 'NEXT_PUBLIC_API_BASE_URL'
          value: 'https://${fraudApi.properties.configuration.ingress.fqdn}'
        }
      ]
    }
  }
}

// ✅ FIX: Grant Dashboard access to Key Vault
resource kvRoleAssignmentDashboard 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, dashboardApp.id, 'Key Vault Secrets User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: dashboardApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

//
// Outputs
//

output dashboardUrl string = 'https://${dashboardApp.properties.defaultHostName}'
output apiUrl string = 'https://${fraudApi.properties.configuration.ingress.fqdn}'
output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output redisHost string = redis.properties.hostName
output keyVaultUri string = keyVault.properties.vaultUri
output logAnalyticsWorkspaceId string = logAnalytics.id
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString

// Additional outputs for verification
output postgresVersion string = postgres.properties.version
output apiMinReplicas int = fraudApi.properties.template.scale.minReplicas
output apiMaxReplicas int = fraudApi.properties.template.scale.maxReplicas
output apiTargetPort int = fraudApi.properties.configuration.ingress.targetPort
