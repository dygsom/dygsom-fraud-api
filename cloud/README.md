# DYGSOM Fraud API - Azure Cloud Deployment

This directory contains all the necessary files and documentation for deploying the DYGSOM Fraud API to Microsoft Azure using Infrastructure as Code (Bicep) and Azure Developer CLI.

## 📋 Prerequisites

Before deploying, ensure you have the following tools installed:

1. **Azure CLI** (`az` command)
   ```bash
   # Install Azure CLI
   # Windows: winget install Microsoft.AzureCLI
   # macOS: brew install azure-cli
   # Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Verify installation
   az --version
   ```

2. **Azure Developer CLI** (`azd` command)
   ```bash
   # Install Azure Developer CLI
   # Windows: winget install Microsoft.AzureDeveloperCLI
   # macOS: brew install azure-dev
   # Linux: curl -fsSL https://aka.ms/install-azd.sh | bash
   
   # Verify installation
   azd version
   ```

3. **Docker** (for containerization)
   ```bash
   # Install Docker Desktop from https://docker.com/products/docker-desktop
   # Verify installation
   docker --version
   ```

## 🏗️ Architecture Overview

The deployment creates the following Azure resources:

- **Azure Container Apps**: Hosts the FastAPI application with auto-scaling (0-3 instances)
- **PostgreSQL Flexible Server**: Database with B1ms tier (burstable, cost-optimized)
- **Azure Cache for Redis**: C0 Basic tier for caching
- **Azure Key Vault**: Secure secret management
- **Application Insights**: Application monitoring and logging
- **Log Analytics Workspace**: Centralized logging
- **Container Registry**: Private container image storage
- **User-Assigned Managed Identity**: Secure service-to-service authentication
- **Storage Account**: Additional storage with security hardening

## 💰 Cost Estimation

**MVP Configuration (0-1K users/month)**:
- Container Apps (0.25 vCPU, 0.5GB): ~$0-15/month (scale to zero)
- PostgreSQL B1ms: ~$12-25/month (burstable)
- Redis C0 Basic: ~$16/month
- Application Insights: ~$5-10/month
- Other services: ~$5-15/month
- **Total: $38-81/month**

**Production Configuration (1K-10K users/month)**:
- Container Apps (sustained): ~$25-50/month
- PostgreSQL with backup: ~$25-40/month
- Redis with monitoring: ~$20-30/month
- Enhanced monitoring: ~$15-25/month
- **Total: $85-145/month**

## 🚀 Quick Deployment

### Step 1: Setup Environment

1. Navigate to the cloud directory:
   ```bash
   cd cloud
   ```

2. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

3. Edit `.env` file with your configuration:
   ```bash
   AZURE_ENV_NAME="dygsom-dev"           # Your environment name
   AZURE_LOCATION="East US"              # Preferred Azure region
   AZURE_SUBSCRIPTION_ID="your-sub-id"   # Your subscription ID (optional)
   ```

### Step 2: Login to Azure

```bash
az login
```

### Step 3: Deploy

**Windows:**
```cmd
deploy.bat
```

**Linux/macOS:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Manual deployment:**
```bash
azd up
```

## 📁 File Structure

```
cloud/
├── azure.yaml                    # Azure Developer CLI configuration
├── .env.template                 # Environment variables template
├── .env                         # Your environment configuration (create from template)
├── deploy.sh                    # Linux/macOS deployment script  
├── deploy.bat                   # Windows deployment script
├── infra/
│   ├── main.bicep              # Main Bicep infrastructure template
│   └── main.parameters.json    # Bicep parameters file
├── AZURE_DEPLOYMENT_PLAN.md     # Comprehensive deployment guide
├── AZURE_COST_ANALYSIS.md       # Detailed cost analysis
└── README.md                    # This file
```

## ⚙️ Configuration Details

### Azure Services Configuration

1. **Container Apps**:
   - Auto-scaling: 0-3 instances based on HTTP requests
   - CPU: 0.25 cores per instance
   - Memory: 0.5GB per instance
   - Ingress: External with CORS enabled

2. **PostgreSQL Flexible Server**:
   - Tier: Burstable B1ms (1 vCore, 2GB RAM)
   - Storage: 32GB with auto-grow
   - Backup: 7 days retention
   - High Availability: Disabled (MVP cost optimization)

3. **Redis Cache**:
   - Tier: Basic C0 (250MB)
   - SSL/TLS: Required
   - MaxMemory Policy: allkeys-lru

4. **Security**:
   - Managed Identity for secure authentication
   - Key Vault for secret management
   - Disabled storage account key access
   - Disabled public blob access

### Environment Variables

The following environment variables are automatically configured:

- `DATABASE_URL`: PostgreSQL connection string (from Key Vault)
- `REDIS_URL`: Redis connection string (from Key Vault) 
- `JWT_SECRET`: Secure JWT signing key (generated)
- `APPLICATIONINSIGHTS_CONNECTION_STRING`: Monitoring configuration
- `ENVIRONMENT`: Set to "production"

## 🔧 Management Commands

### View Deployment Status
```bash
azd show
```

### View Application Logs
```bash
azd logs
```

### Deploy Code Changes Only
```bash
azd deploy
```

### Delete All Resources
```bash
azd down
```

### Monitor Resources
```bash
# View resource group in Azure Portal
az group show --name rg-{AZURE_ENV_NAME} --output table

# View Container App status
az containerapp show --name ca{unique-token} --resource-group rg-{AZURE_ENV_NAME}
```

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   # Re-login to Azure
   az login
   
   # Check current account
   az account show
   ```

2. **Resource Name Conflicts**:
   - Change `AZURE_ENV_NAME` in `.env` file
   - Resource names are generated with unique tokens

3. **Docker Build Failures**:
   ```bash
   # Verify Docker is running
   docker ps
   
   # Login to container registry
   az acr login --name {registry-name}
   ```

4. **Permission Errors**:
   ```bash
   # Check subscription access
   az account list --output table
   
   # Set correct subscription
   az account set --subscription {subscription-id}
   ```

### Log Analysis

1. **View Container App Logs**:
   ```bash
   azd logs --service api
   ```

2. **View Infrastructure Logs**:
   - Go to Azure Portal → Log Analytics Workspace
   - Query: `ContainerAppConsoleLogs_CL`

3. **Monitor Performance**:
   - Azure Portal → Application Insights
   - View metrics, traces, and failures

## 🛡️ Security Considerations

1. **Managed Identity**: All service-to-service authentication uses managed identity
2. **Key Vault**: All secrets stored securely in Azure Key Vault
3. **Network Security**: Private endpoints for database connections
4. **TLS/SSL**: All connections encrypted in transit
5. **Access Control**: Minimal required permissions via RBAC

## 📊 Monitoring and Alerts

The deployment includes comprehensive monitoring:

1. **Application Insights**: Application performance monitoring
2. **Log Analytics**: Centralized logging and querying
3. **Container Apps Metrics**: CPU, memory, and request metrics
4. **Database Monitoring**: Connection and performance metrics

### Recommended Alerts

Set up alerts for:
- High CPU usage (>80%)
- High memory usage (>90%)
- Failed requests (>5%)
- Database connection failures
- High response times (>2 seconds)

## 🔄 CI/CD Integration

For automated deployments, integrate with GitHub Actions:

1. Create `.github/workflows/azure-deploy.yml`
2. Add Azure service principal secrets
3. Use `azd deploy` in workflow

Example workflow:
```yaml
name: Deploy to Azure
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Azure
        run: |
          cd cloud
          azd deploy --no-prompt
        env:
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Container Apps automatically scale 0-3 instances
- Increase `maxReplicas` in `main.bicep` for higher scale
- Consider switching to Standard tier for production

### Database Scaling
- Current B1ms tier supports up to ~1K concurrent connections
- Upgrade to General Purpose for higher performance
- Enable read replicas for read-heavy workloads

### Cost Optimization
- Monitor usage patterns via Application Insights
- Adjust scaling rules based on actual traffic
- Consider reserved instances for production workloads

## 🆘 Support

For deployment issues:

1. **Check Azure Status**: https://status.azure.com/
2. **Azure Support**: Create support ticket in Azure Portal
3. **Community**: Azure Developer CLI GitHub discussions
4. **Documentation**: https://docs.microsoft.com/azure/developer/azure-developer-cli/

## 📝 Next Steps

After successful deployment:

1. **Configure Custom Domain**: Add your domain to Container Apps
2. **SSL Certificate**: Set up managed SSL certificate
3. **API Management**: Consider Azure API Management for production
4. **Backup Strategy**: Configure database backup policies
5. **Disaster Recovery**: Set up geo-redundant backups
6. **Performance Testing**: Load test your API endpoints
7. **Security Review**: Conduct security assessment