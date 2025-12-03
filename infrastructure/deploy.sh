#!/bin/bash
set -e  # Exit on error

#######################################################################
# DYGSOM Fraud Detection - Deployment Script
# Despliega infraestructura a Azure usando Bicep
#######################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP=""
ENV_NAME="dev"
LOCATION="eastus"
BICEP_FILE="dygsom-fraud-main.bicep"
PARAMS_FILE="dygsom-fraud-main.parameters.json"
VALIDATE_ONLY=false

#######################################################################
# Helper Functions
#######################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

show_usage() {
    cat << EOF
Usage: ./deploy.sh [OPTIONS]

Despliega la infraestructura de DYGSOM Fraud Detection a Azure.

OPTIONS:
    -g, --resource-group NAME    Nombre del Resource Group (requerido)
    -e, --env ENV                Ambiente: dev, qa, prod (default: dev)
    -l, --location LOCATION      Azure region (default: eastus)
    -f, --bicep-file FILE        Archivo Bicep (default: dygsom-fraud-main.bicep)
    -p, --params-file FILE       Archivo de parámetros (default: dygsom-fraud-main.parameters.json)
    -v, --validate-only          Solo validar, no desplegar
    -h, --help                   Mostrar esta ayuda

EXAMPLES:
    # Desplegar a dev
    ./deploy.sh -g rg-dygsom-fraud-dev -e dev

    # Desplegar a producción en West Europe
    ./deploy.sh -g rg-dygsom-fraud-prod -e prod -l westeurope

    # Solo validar template
    ./deploy.sh -g rg-dygsom-fraud-dev --validate-only

PREREQUISITES:
    - Azure CLI instalado (az)
    - Sesión autenticada (az login)
    - Permisos para crear recursos en suscripción
    - Archivo de parámetros configurado con valores correctos

EOF
}

#######################################################################
# Parse Arguments
#######################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -e|--env)
            ENV_NAME="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -f|--bicep-file)
            BICEP_FILE="$2"
            shift 2
            ;;
        -p|--params-file)
            PARAMS_FILE="$2"
            shift 2
            ;;
        -v|--validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_usage
            exit 1
            ;;
    esac
done

#######################################################################
# Validate Prerequisites
#######################################################################

print_header "Validando prerequisitos"

# Check if resource group is provided
if [ -z "$RESOURCE_GROUP" ]; then
    print_error "Resource group es requerido. Usa -g o --resource-group"
    show_usage
    exit 1
fi

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI no está instalado. Instalar desde: https://learn.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi
print_success "Azure CLI encontrado"

# Check if logged in
if ! az account show &> /dev/null; then
    print_error "No estás autenticado. Ejecuta: az login"
    exit 1
fi
print_success "Sesión de Azure autenticada"

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
print_info "Suscripción activa: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# Check if Bicep file exists
if [ ! -f "$BICEP_FILE" ]; then
    print_error "Archivo Bicep no encontrado: $BICEP_FILE"
    exit 1
fi
print_success "Archivo Bicep encontrado: $BICEP_FILE"

# Check if parameters file exists
if [ ! -f "$PARAMS_FILE" ]; then
    print_error "Archivo de parámetros no encontrado: $PARAMS_FILE"
    exit 1
fi
print_success "Archivo de parámetros encontrado: $PARAMS_FILE"

#######################################################################
# Create Resource Group
#######################################################################

print_header "Configurando Resource Group"

if az group exists --name "$RESOURCE_GROUP" | grep -q true; then
    print_warning "Resource group '$RESOURCE_GROUP' ya existe"
    EXISTING_LOCATION=$(az group show --name "$RESOURCE_GROUP" --query location -o tsv)
    print_info "Ubicación actual: $EXISTING_LOCATION"

    if [ "$EXISTING_LOCATION" != "$LOCATION" ]; then
        print_warning "La ubicación solicitada ($LOCATION) difiere de la existente ($EXISTING_LOCATION)"
        print_warning "Se usará la ubicación existente: $EXISTING_LOCATION"
        LOCATION=$EXISTING_LOCATION
    fi
else
    print_info "Creando resource group '$RESOURCE_GROUP' en $LOCATION..."
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
    print_success "Resource group creado"
fi

#######################################################################
# Validate Template
#######################################################################

print_header "Validando plantilla Bicep"

VALIDATION_OUTPUT=$(mktemp)
if az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$BICEP_FILE" \
    --parameters "@$PARAMS_FILE" \
    --parameters location="$LOCATION" envName="$ENV_NAME" \
    > "$VALIDATION_OUTPUT" 2>&1; then
    print_success "Validación exitosa"
else
    print_error "Validación fallida:"
    cat "$VALIDATION_OUTPUT"
    rm "$VALIDATION_OUTPUT"
    exit 1
fi
rm "$VALIDATION_OUTPUT"

if [ "$VALIDATE_ONLY" = true ]; then
    print_success "Validación completada. No se desplegó infraestructura (--validate-only)"
    exit 0
fi

#######################################################################
# Confirm Deployment
#######################################################################

print_header "Confirmación de Despliegue"

echo -e "${YELLOW}Estás a punto de desplegar:${NC}"
echo -e "  Resource Group: ${GREEN}$RESOURCE_GROUP${NC}"
echo -e "  Ambiente:       ${GREEN}$ENV_NAME${NC}"
echo -e "  Ubicación:      ${GREEN}$LOCATION${NC}"
echo -e "  Bicep File:     ${GREEN}$BICEP_FILE${NC}"
echo -e "  Parámetros:     ${GREEN}$PARAMS_FILE${NC}"
echo ""

read -p "¿Continuar con el despliegue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Despliegue cancelado por el usuario"
    exit 0
fi

#######################################################################
# Deploy Infrastructure
#######################################################################

print_header "Desplegando Infraestructura"

DEPLOYMENT_NAME="dygsom-fraud-$(date +%Y%m%d-%H%M%S)"
print_info "Nombre de despliegue: $DEPLOYMENT_NAME"
print_info "Tiempo estimado: 10-15 minutos..."

echo ""
if az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$BICEP_FILE" \
    --parameters "@$PARAMS_FILE" \
    --parameters location="$LOCATION" envName="$ENV_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --output json > deployment-output.json; then

    print_success "Despliegue completado exitosamente!"

    #######################################################################
    # Display Outputs
    #######################################################################

    print_header "Recursos Desplegados"

    # Parse outputs
    DASHBOARD_URL=$(jq -r '.properties.outputs.dashboardUrl.value // "N/A"' deployment-output.json)
    API_URL=$(jq -r '.properties.outputs.apiUrl.value // "N/A"' deployment-output.json)
    POSTGRES_FQDN=$(jq -r '.properties.outputs.postgresFqdn.value // "N/A"' deployment-output.json)
    REDIS_HOST=$(jq -r '.properties.outputs.redisHost.value // "N/A"' deployment-output.json)
    KEYVAULT_URI=$(jq -r '.properties.outputs.keyVaultUri.value // "N/A"' deployment-output.json)

    echo -e "${GREEN}Dashboard URL:${NC}    $DASHBOARD_URL"
    echo -e "${GREEN}API URL:${NC}          $API_URL"
    echo -e "${GREEN}PostgreSQL FQDN:${NC}  $POSTGRES_FQDN"
    echo -e "${GREEN}Redis Host:${NC}       $REDIS_HOST"
    echo -e "${GREEN}Key Vault URI:${NC}    $KEYVAULT_URI"

    #######################################################################
    # Next Steps
    #######################################################################

    print_header "Próximos Pasos"

    echo "1. Ejecutar migraciones de base de datos:"
    echo -e "   ${BLUE}az containerapp exec \\${NC}"
    echo -e "   ${BLUE}  --resource-group $RESOURCE_GROUP \\${NC}"
    echo -e "   ${BLUE}  --name ca-dygsom-fraud-api-$ENV_NAME \\${NC}"
    echo -e "   ${BLUE}  --command \"/bin/sh -c 'prisma migrate deploy'\"${NC}"
    echo ""

    echo "2. Verificar health de la API:"
    echo -e "   ${BLUE}curl $API_URL/health${NC}"
    echo ""

    echo "3. Ver logs en tiempo real:"
    echo -e "   ${BLUE}az containerapp logs show \\${NC}"
    echo -e "   ${BLUE}  --resource-group $RESOURCE_GROUP \\${NC}"
    echo -e "   ${BLUE}  --name ca-dygsom-fraud-api-$ENV_NAME \\${NC}"
    echo -e "   ${BLUE}  --follow${NC}"
    echo ""

    echo "4. Acceder al dashboard:"
    echo -e "   ${BLUE}$DASHBOARD_URL${NC}"
    echo ""

    echo "5. Ver documentación de API:"
    echo -e "   ${BLUE}$API_URL/docs${NC}"
    echo ""

    # Save outputs to file
    OUTPUTS_FILE="deployment-outputs-$ENV_NAME.txt"
    cat > "$OUTPUTS_FILE" << EOF
DYGSOM Fraud Detection - Deployment Outputs
Environment: $ENV_NAME
Deployed: $(date)
Deployment Name: $DEPLOYMENT_NAME

Dashboard URL:    $DASHBOARD_URL
API URL:          $API_URL
PostgreSQL FQDN:  $POSTGRES_FQDN
Redis Host:       $REDIS_HOST
Key Vault URI:    $KEYVAULT_URI
EOF

    print_success "Outputs guardados en: $OUTPUTS_FILE"

else
    print_error "Despliegue fallido. Revisa el output arriba para detalles."
    exit 1
fi

print_header "Despliegue Finalizado"
print_success "¡Infraestructura desplegada exitosamente!"
