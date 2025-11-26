#!/bin/bash

################################################################################
# Deployment Script for DYGSOM Fraud API
# Usage: ./deploy.sh [staging|production] [version]
#
# This script handles the complete deployment process:
# 1. Load environment configuration
# 2. Pull Docker image
# 3. Backup current deployment
# 4. Run database migrations
# 5. Deploy with docker compose
# 6. Health check with retries
# 7. Rollback if health check fails
# 8. Cleanup old images
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_HEALTH_CHECK_RETRIES=5
HEALTH_CHECK_DELAY=5
STARTUP_WAIT=15

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_usage() {
    echo "Usage: $0 [staging|production] [version]"
    echo ""
    echo "Arguments:"
    echo "  environment  - Target environment (staging or production)"
    echo "  version      - Docker image version/tag to deploy"
    echo ""
    echo "Examples:"
    echo "  $0 staging staging-latest"
    echo "  $0 production v1.0.0"
    exit 1
}

health_check() {
    local url=$1
    local retries=0

    log_info "Running health checks on $url..."

    while [ $retries -lt $MAX_HEALTH_CHECK_RETRIES ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "Health check passed!"
            return 0
        else
            retries=$((retries + 1))
            log_warning "Health check failed (attempt $retries/$MAX_HEALTH_CHECK_RETRIES)"

            if [ $retries -lt $MAX_HEALTH_CHECK_RETRIES ]; then
                sleep $HEALTH_CHECK_DELAY
            fi
        fi
    done

    log_error "Health check failed after $MAX_HEALTH_CHECK_RETRIES attempts"
    return 1
}

create_backup() {
    local backup_dir=$1

    log_info "Creating backup of current deployment..."

    mkdir -p "$backup_dir"

    local backup_file="$backup_dir/backup-$(date +%Y%m%d-%H%M%S).tar.gz"

    # Save current docker-compose state
    docker compose ps -a > "$backup_dir/containers-$(date +%Y%m%d-%H%M%S).txt" || true

    # Create tarball of configuration
    tar -czf "$backup_file" docker-compose.yml .env 2>/dev/null || true

    log_success "Backup created: $backup_file"

    # Keep only last 10 backups
    ls -t "$backup_dir"/backup-*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm || true
}

rollback_deployment() {
    log_error "Deployment failed! Starting rollback..."

    # Try to restore previous containers
    docker compose up -d --force-recreate --no-deps api || true

    log_warning "Rollback attempted. Please check logs and verify service status."
    log_info "Use './rollback.sh $ENVIRONMENT' for manual rollback to a specific backup."
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."

    # Remove dangling images
    docker image prune -f > /dev/null 2>&1 || true

    log_success "Cleanup completed"
}

################################################################################
# Main Deployment Logic
################################################################################

main() {
    # Validate arguments
    if [ $# -lt 2 ]; then
        log_error "Missing required arguments"
        print_usage
    fi

    ENVIRONMENT=$1
    VERSION=$2

    # Validate environment
    if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
        log_error "Invalid environment: $ENVIRONMENT"
        print_usage
    fi

    log_info "=========================================="
    log_info "  DYGSOM Fraud API Deployment"
    log_info "=========================================="
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    log_info "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "=========================================="
    echo ""

    # Navigate to deployment directory
    DEPLOY_DIR="/opt/dygsom-fraud-api/deployment/$ENVIRONMENT"

    if [ ! -d "$DEPLOY_DIR" ]; then
        log_error "Deployment directory not found: $DEPLOY_DIR"
        exit 1
    fi

    cd "$DEPLOY_DIR"
    log_success "Changed to deployment directory: $DEPLOY_DIR"

    # Load environment variables
    if [ -f ".env" ]; then
        source .env
        log_success "Environment variables loaded"
    else
        log_warning ".env file not found, using defaults"
    fi

    # Set Docker image variables
    export IMAGE_TAG="$VERSION"

    # Create backup
    BACKUP_DIR="/opt/dygsom-fraud-api/backups"
    create_backup "$BACKUP_DIR"

    # Pull Docker image
    log_info "Pulling Docker image: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${VERSION}"

    if ! docker pull "${DOCKER_REGISTRY}/${IMAGE_NAME}:${VERSION}"; then
        log_error "Failed to pull Docker image"
        exit 1
    fi

    log_success "Docker image pulled successfully"

    # Run database migrations
    log_info "Running database migrations..."

    if ! docker compose run --rm api npx prisma migrate deploy; then
        log_error "Database migrations failed"
        exit 1
    fi

    log_success "Database migrations completed"

    # Deploy with docker compose
    log_info "Deploying new version..."

    if ! docker compose up -d --force-recreate --no-deps api; then
        log_error "Docker compose deployment failed"
        rollback_deployment
        exit 1
    fi

    log_success "New version deployed"

    # Wait for service to start
    log_info "Waiting ${STARTUP_WAIT}s for service to start..."
    sleep $STARTUP_WAIT

    # Health check
    if ! health_check "http://localhost:3000/health/ready"; then
        log_error "Health check failed!"

        # Show logs for debugging
        log_info "Showing recent logs:"
        docker compose logs --tail=50 api

        # Rollback
        rollback_deployment
        exit 1
    fi

    # Cleanup old images
    cleanup_old_images

    # Final success message
    echo ""
    log_info "=========================================="
    log_success "Deployment completed successfully!"
    log_info "=========================================="
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    log_info "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "=========================================="
    echo ""

    # Show running containers
    log_info "Running containers:"
    docker compose ps

    exit 0
}

# Run main function
main "$@"
