# 🚀 AWS Migration Template - DYGSOM Fraud Detection

**Estado**: 📋 Template preparado para migración futura
**Arquitectura equivalente**: ECS Fargate + RDS + ElastiCache
**Migración estimada**: 2-3 días
**Compatibilidad**: 100% (Docker-based)

---

## 🔄 **MAPEO AZURE → AWS**

### Servicios Equivalentes

| Componente Actual (Azure)     | AWS Equivalente   | Migración             | Costo AWS Est. |
|-------------------------------|-------------------|-----------------------|----------------|
| **Container Apps**            | ECS Fargate       | ✅ Docker compatible  | $30-40/mes    |
| **PostgreSQL Flexible**       | RDS PostgreSQL    | ✅ pg_dump/restore    | $25-35/mes    |
| **Redis Cache**               | ElastiCache Redis | ✅ Compatible         | $15-20/mes    |
| **GitHub Container Registry** | ECR               | 🔄 Registry change    | $2-5/mes      |
| **Azure DNS**                 | Route 53          | 🔄 DNS migration      | $1-2/mes      |

**Total AWS**: ~$73-102/mes (vs $55-61 Azure actual)

---

## 🏗️ **Arquitectura AWS Target**

```
┌─────────────────────────────────────────────────────────┐
│                    VPC (us-east-1)                      │
│  ┌────────────────────┐    ┌──────────────────────┐    │
│  │ ECS Fargate        │    │ Application Load     │    │
│  │ - API Task         │◄───│ Balancer (ALB)       │    │
│  │ - Dashboard Task   │    │ - SSL Termination    │    │
│  │ - Auto Scaling     │    │ - Health Checks      │    │
│  └────────────────────┘    └──────────────────────┘    │
│            │                         │                   │
│            └────────┬────────────────┘                   │
│                     ▼                                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │              RDS PostgreSQL                      │    │
│  │  ┌─────────────┐       ┌──────────────────┐     │    │
│  │  │ Primary DB  │◄──────│ ElastiCache      │     │    │
│  │  │ Multi-AZ    │       │ Redis Cluster    │     │    │
│  │  └─────────────┘       └──────────────────┘     │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 **PLAN DE MIGRACIÓN PASO A PASO**

### Fase 1: Preparación (Día 1)

#### 1.1 Configurar AWS Infrastructure

```bash
# 1. Crear VPC y Subnets
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=dygsom-fraud-vpc}]'

# 2. Crear ECS Cluster
aws ecs create-cluster --cluster-name dygsom-fraud-cluster --capacity-providers FARGATE

# 3. Crear ECR Repository
aws ecr create-repository --repository-name dygsom/fraud-api --region us-east-1
```

#### 1.2 Configurar RDS PostgreSQL

```bash
# Crear RDS instance
aws rds create-db-instance \
    --db-instance-identifier dygsom-fraud-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.3 \
    --allocated-storage 20 \
    --db-name frauddb \
    --master-username postgres \
    --master-user-password 'PgpassStrong123!' \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-subnet-group-name dygsom-fraud-subnet-group \
    --backup-retention-period 7 \
    --storage-encrypted
```

#### 1.3 Configurar ElastiCache Redis

```bash
# Crear Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id dygsom-fraud-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    --cache-subnet-group-name dygsom-fraud-cache-subnet \
    --security-group-ids sg-xxxxxxxxx
```

### Fase 2: Migración de Datos (Día 2)

#### 2.1 Migrar Base de Datos

```bash
# 1. Backup desde Azure
pg_dump -h psql-dygsom-dev.postgres.database.azure.com \
        -U postgres -d frauddb > azure_backup.sql

# 2. Restore en AWS RDS
psql -h dygsom-fraud-db.xxxxxxxxx.us-east-1.rds.amazonaws.com \
     -U postgres -d frauddb < azure_backup.sql
```

#### 2.2 Configurar GitHub Actions para AWS

```yaml
# .github/workflows/aws-deploy.yml
name: Deploy to AWS ECS

on:
  push:
    branches: [aws-migration]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: dygsom/fraud-api

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

    - name: Deploy to ECS
      uses: aws-actions/amazon-ecs-deploy-task-definition@v1
      with:
        task-definition: task-definition.json
        service: dygsom-fraud-api-service
        cluster: dygsom-fraud-cluster
```

### Fase 3: Deployment y Testing (Día 3)

#### 3.1 ECS Task Definitions

```json
{
  "family": "dygsom-fraud-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "account.dkr.ecr.us-east-1.amazonaws.com/dygsom/fraud-api:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://postgres:password@rds-endpoint:5432/frauddb"
        },
        {
          "name": "REDIS_URL", 
          "value": "redis://elasticache-endpoint:6379"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dygsom-fraud-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 3.2 Application Load Balancer

```bash
# Crear ALB
aws elbv2 create-load-balancer \
    --name dygsom-fraud-alb \
    --subnets subnet-xxxxxxxx subnet-yyyyyyyy \
    --security-groups sg-xxxxxxxxx \
    --scheme internet-facing \
    --type application

# Crear Target Group
aws elbv2 create-target-group \
    --name dygsom-fraud-targets \
    --protocol HTTP \
    --port 3000 \
    --vpc-id vpc-xxxxxxxxx \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --healthy-threshold-count 2
```

---

## 🔧 **CONFIGURACIÓN CI/CD AWS**

### GitHub Actions Secrets Requeridos

```bash
# Agregar a GitHub Secrets:
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_ACCOUNT_ID=123456789012
```

### Terraform Template (Opcional)

```hcl
# infrastructure/aws/main.tf
provider "aws" {
  region = "us-east-1"
}

resource "aws_ecs_cluster" "fraud_cluster" {
  name = "dygsom-fraud-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_db_instance" "fraud_db" {
  identifier = "dygsom-fraud-db"
  engine     = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  
  db_name  = "frauddb"
  username = "postgres"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.fraud.name
  
  backup_retention_period = 7
  storage_encrypted = true
  
  tags = {
    Name = "DYGSOM Fraud Database"
  }
}
```

---

## 📊 **COMPARACIÓN DETALLADA: AZURE vs AWS**

### Costos Mensuales Estimados

| Componente | Azure (Actual) | AWS (Estimado) | Diferencia |
|-----------|----------------|----------------|------------|
| **Compute** | $35-40 | $30-35 | -$5 |
| **Database** | $15-18 | $25-30 | +$10 |
| **Cache** | $3-5 | $15-20 | +$15 |
| **Networking** | $0-2 | $5-8 | +$5 |
| **Storage** | $2-3 | $3-5 | +$2 |
| **Monitoring** | Incluido | $5-10 | +$10 |
| **TOTAL** | **$55-61** | **$83-108** | **+$28-47** |

### Ventajas AWS

✅ **Mayor ecosistema de servicios**
✅ **Mejor integración con terceros**  
✅ **Más opciones de compute (Lambda, etc.)**
✅ **Networking más avanzado**

### Ventajas Azure (Current)

✅ **Menor costo overall**
✅ **Simplicidad de Container Apps**
✅ **Mejor integración GitHub**
✅ **Menos configuración de red**

---

## 🎯 **CUÁNDO MIGRAR A AWS**

### Triggers para Migración

1. **Escala > 10,000 requests/min**
2. **Necesidad servicios AWS específicos** (Lambda, SageMaker)
3. **Compliance requirements** (AWS GovCloud)
4. **Multi-region deployment** requerido
5. **Presupuesto > $500/mes** (economics of scale)

### Cronograma Sugerido

```
Phase 1: Preparation    [1-2 días]
Phase 2: Data Migration [1 día] 
Phase 3: App Migration  [1 día]
Phase 4: DNS Cutover    [4 horas]
Phase 5: Validation     [1 día]
```

**Total tiempo**: 5-6 días
**Downtime**: < 4 horas (solo DNS cutover)

---

## 📞 **Support y Referencias**

**AWS Documentation**:
- ECS Fargate: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html
- RDS PostgreSQL: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html
- ElastiCache: https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/

**Migration Tools**:
- AWS Database Migration Service: https://aws.amazon.com/dms/
- Container Migration: https://docs.aws.amazon.com/containers/

**Monitoring**:
- CloudWatch: https://docs.aws.amazon.com/cloudwatch/
- X-Ray Tracing: https://docs.aws.amazon.com/xray/