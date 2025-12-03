// ================================================================================
// DYGSOM Fraud Detection - MVP Architecture
// ================================================================================
// Optimized for: Cost, Simplicity, Single Deployment
// Region: brazilsouth (optimal latency from Lima, Peru ~30-40ms)
// Total Cost: ~$45/month
// ================================================================================

targetScope = 'resourceGroup'

// ================================================================================
// PARAMETERS
// ================================================================================

@description('Azure region for all resources (brazilsouth recommended for Lima, Peru)')
param location string = resourceGroup().location

@description('Environment name')
@allowed([
  'dev'
  'qa'
  'prod'
])
param envName string = 'dev'

@description('Docker image for API from GitHub Container Registry')
param apiImage string = 'ghcr.io/dygsom/dygsom-fraud-api:main'

@description('Docker image for Dashboard from GitHub Container Registry')
param dashboardImage string = 'ghcr.io/dygsom/dygsom-fraud-dashboard:main'

@description('PostgreSQL admin username')
param postgresAdminUser string = 'pgadmin'

@secure()
@description('PostgreSQL admin password (min 8 chars, letters + numbers + symbols)')
param postgresAdminPassword string

@description('PostgreSQL database name')
param postgresDatabaseName string = 'dygsom_fraud'

@description('Enable Redis cache (set to false to save $16/month)')
param enableRedis bool = true

// ================================================================================
// CONTAINER APPS ENVIRONMENT
// ================================================================================

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-dygsom-${envName}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ================================================================================
// LOG ANALYTICS (Minimal for Container Apps logs)
// ================================================================================

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'law-dygsom-${envName}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// ================================================================================
// POSTGRESQL FLEXIBLE SERVER
// ================================================================================

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: 'pg-dygsom-${envName}'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    administratorLogin: postgresAdminUser
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

// Create database
resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-12-01' = {
  parent: postgres
  name: postgresDatabaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Firewall rule: Allow Azure services
resource postgresFirewallAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2022-12-01' = {
  parent: postgres
  name: 'AllowAllAzureServicesAndResourcesWithinAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ================================================================================
// REDIS CACHE (Optional - can be disabled to save costs)
// ================================================================================

resource redis 'Microsoft.Cache/redis@2023-04-01' = if (enableRedis) {
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
    redisConfiguration: {
      'maxmemory-policy': 'allkeys-lru'
    }
  }
}

// ================================================================================
// API CONTAINER APP (FastAPI)
// ================================================================================

resource apiContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-api-${envName}'
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'http'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
        corsPolicy: {
          allowedOrigins: [
            'https://${dashboardContainerApp.properties.configuration.ingress.fqdn}'
            'http://localhost:3001'
          ]
          allowedMethods: [
            'GET'
            'POST'
            'PUT'
            'DELETE'
            'OPTIONS'
          ]
          allowedHeaders: [
            '*'
          ]
          maxAge: 3600
        }
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              value: 'postgresql://${postgresAdminUser}:${postgresAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${postgresDatabaseName}?sslmode=require'
            }
            {
              name: 'REDIS_URL'
              value: enableRedis ? 'rediss://:${redis.listKeys().primaryKey}@${redis.properties.hostName}:${redis.properties.sslPort}/0?ssl_cert_reqs=required' : ''
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
            {
              name: 'ENVIRONMENT'
              value: envName
            }
            {
              name: 'API_KEY_SALT'
              value: uniqueString(resourceGroup().id, 'api-key-salt')
            }
            {
              name: 'JWT_SECRET_KEY'
              value: uniqueString(resourceGroup().id, 'jwt-secret')
            }
            {
              name: 'ENABLE_SWAGGER'
              value: 'true'
            }
            {
              name: 'CORS_ORIGINS'
              value: 'https://${dashboardContainerApp.properties.configuration.ingress.fqdn},http://localhost:3001'
            }
          ]
          probes: [
            {
              type: 'Liveness'
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
              type: 'Readiness'
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
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
        ]
      }
    }
  }
}

// ================================================================================
// DASHBOARD CONTAINER APP (Next.js)
// ================================================================================

resource dashboardContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-dashboard-${envName}'
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3001
        transport: 'http'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
    }
    template: {
      containers: [
        {
          name: 'dashboard'
          image: dashboardImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'NEXT_PUBLIC_API_BASE_URL'
              value: 'https://${apiContainerApp.properties.configuration.ingress.fqdn}'
            }
            {
              name: 'NODE_ENV'
              value: 'production'
            }
            {
              name: 'PORT'
              value: '3001'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: 3001
                scheme: 'HTTP'
              }
              initialDelaySeconds: 15
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// ================================================================================
// OUTPUTS
// ================================================================================

output apiUrl string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}'
output dashboardUrl string = 'https://${dashboardContainerApp.properties.configuration.ingress.fqdn}'
output apiSwaggerUrl string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}/docs'
output postgresHost string = postgres.properties.fullyQualifiedDomainName
output postgresDatabaseName string = postgresDatabaseName
output redisHost string = enableRedis ? redis.properties.hostName : 'disabled'
output containerAppsEnvironment string = containerAppsEnv.name
output region string = location
output estimatedMonthlyCost string = enableRedis ? '$45-50 USD' : '$30-35 USD'
